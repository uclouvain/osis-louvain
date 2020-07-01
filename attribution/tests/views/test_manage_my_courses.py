##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
from unittest import mock
from unittest.mock import patch

from django.contrib import messages
from django.contrib.auth.models import Permission
from django.http import HttpResponse, HttpResponseNotFound
from django.test import RequestFactory
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _
from waffle.testutils import override_flag

from attribution.tests.factories.attribution import AttributionFactory
from attribution.views.manage_my_courses import list_my_attributions_summary_editable, view_educational_information
from base.models.enums import academic_calendar_type
from base.models.enums.entity_type import FACULTY
from base.models.enums.learning_unit_year_subtypes import FULL
from base.tests.factories.academic_calendar import AcademicCalendarFactory, OpenAcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.teaching_material import TeachingMaterialFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.utils.get_messages import get_messages_from_response
from osis_common.utils.perms import BasePerm


class ManageMyCoursesViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.user = cls.person.user
        cls.tutor = TutorFactory(person=cls.person)
        cls.current_ac_year = create_current_academic_year()
        ac_year_in_past = AcademicYearFactory.produce_in_past(cls.current_ac_year.year)
        cls.ac_year_in_future = AcademicYearFactory.produce_in_future(cls.current_ac_year.year)

        cls.academic_calendar = OpenAcademicCalendarFactory(
            academic_year=cls.current_ac_year,
            data_year=cls.current_ac_year,
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
        )
        requirement_entity = EntityVersionFactory().entity
        # Create multiple attribution in different academic years
        for ac_year in ac_year_in_past + [cls.current_ac_year] + cls.ac_year_in_future:
            learning_container_year = LearningContainerYearFactory(
                academic_year=ac_year,
                requirement_entity=requirement_entity
            )
            learning_unit_year = LearningUnitYearFactory(
                summary_locked=False,
                academic_year=ac_year,
                learning_container_year=learning_container_year
            )
            AttributionFactory(
                tutor=cls.tutor,
                summary_responsible=True,
                learning_unit_year=learning_unit_year,
            )
        cls.url = reverse(list_my_attributions_summary_editable)

    def setUp(self):
        self.client.force_login(self.user)

    def test_list_my_attributions_summary_editable_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_list_my_attributions_summary_editable_user_not_tutor(self):
        person_not_tutor = PersonFactory()
        self.client.force_login(person_not_tutor.user)

        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_list_my_attributions_summary_editable(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "manage_my_courses/list_my_courses_summary_editable.html")

        context = response.context
        self.assertIsInstance(context['entity_calendars'], dict)

        for luy, error in context["learning_unit_years_with_errors"]:
            self.assertEqual(luy.academic_year.year, self.current_ac_year.year)
            self.assertFalse(error.errors)

    @patch('base.business.event_perms.EventPerm.is_open', return_value=False)
    def test_list_my_attributions_summary_editable_after_period(self, mock_is_open):
        self.academic_calendar.start_date = datetime.date.today() - datetime.timedelta(weeks=52)
        self.academic_calendar.end_date = datetime.date.today() - datetime.timedelta(weeks=48)
        self.academic_calendar.save()

        next_calendar = AcademicCalendarFactory(
            start_date=datetime.date.today() + datetime.timedelta(weeks=48),
            end_date=datetime.date.today() + datetime.timedelta(weeks=52),
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
        )
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "manage_my_courses/list_my_courses_summary_editable.html")

        context = response.context
        self.assertIsInstance(context['entity_calendars'], dict)

        for luy, error in context["learning_unit_years_with_errors"]:
            self.assertEqual(luy.academic_year.year, self.current_ac_year.year)
            self.assertEqual(error.errors[0], _("Not in period to edit description fiche."))

        msg = get_messages_from_response(response)
        self.assertEqual(
            msg[0].get('message'),
            _('For the academic year %(data_year)s, the summary edition period is ended since %(end_date)s.') % {
                "data_year": self.academic_calendar.data_year,
                "end_date": self.academic_calendar.end_date.strftime('%d-%m-%Y'),
            }
        )
        self.assertEqual(msg[0].get('level'), messages.INFO)
        self.assertEqual(
            msg[1].get('message'),
            _('For the academic year %(data_year)s, the summary edition period will open on %(start_date)s.') % {
                "data_year": next_calendar.data_year,
                "start_date": next_calendar.start_date.strftime('%d-%m-%Y'),
            }
        )
        self.assertEqual(msg[1].get('level'), messages.INFO)

    def test_list_my_attributions_summary_editable_next_data_year(self):
        self.academic_calendar.start_date = datetime.date.today() - datetime.timedelta(weeks=1)
        self.academic_calendar.end_date = datetime.date.today() + datetime.timedelta(weeks=4)
        self.academic_calendar.academic_year = self.ac_year_in_future[1]  # This is n+1
        self.academic_calendar.data_year = self.ac_year_in_future[1]  # This is n+1
        self.academic_calendar.save()

        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "manage_my_courses/list_my_courses_summary_editable.html")

        context = response.context

        for luy, error in context["learning_unit_years_with_errors"]:
            self.assertEqual(luy.academic_year.year, self.ac_year_in_future[1].year)
            self.assertFalse(error.errors)


@override_flag('educational_information_block_action', active=True)
class TestViewEducationalInformation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tutor = TutorFactory()
        cls.attribution = AttributionFactory(tutor=cls.tutor, summary_responsible=True)
        cls.url = reverse(view_educational_information, args=[cls.attribution.learning_unit_year.id])
        cls.tutor.person.user.user_permissions.add(Permission.objects.get(codename='can_edit_learningunit_pedagogy'))

    def setUp(self):
        self.client.force_login(self.tutor.person.user)

        self.patcher_perm_can_view_educational_information = mock.patch(
            'attribution.views.perms.can_tutor_view_educational_information')
        self.mock_perm_view = self.patcher_perm_can_view_educational_information.start()
        self.mock_perm_view.return_value = True

    def tearDown(self):
        self.patcher_perm_can_view_educational_information.stop()

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_check_if_user_can_view_educational_information(self):
        self.mock_perm_view.return_value = False

        response = self.client.get(self.url)

        self.assertTrue(self.mock_perm_view.called)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_template_used(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "manage_my_courses/educational_information.html")

        context = response.context
        self.assertEqual(context["learning_unit_year"], self.attribution.learning_unit_year)
        self.assertTrue("teaching_materials" in context)
        self.assertFalse(context["cms_labels_translated"])
        self.assertFalse(context["can_edit_information"])
        self.assertFalse(context["can_edit_summary_locked_field"])
        self.assertFalse(context["submission_dates"])
        # Verify URL for tutor [==> Specific redirection]
        self.assertEqual(context['create_teaching_material_urlname'], 'tutor_teaching_material_create')
        self.assertEqual(context['update_teaching_material_urlname'], 'tutor_teaching_material_edit')
        self.assertEqual(context['delete_teaching_material_urlname'], 'tutor_teaching_material_delete')
        self.assertEqual(context['update_mobility_modality_urlname'], 'tutor_mobility_modality_update')


class TestManageEducationalInformation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tutor = TutorFactory()
        cls.attribution = AttributionFactory(
            tutor=cls.tutor,
            summary_responsible=True,
            learning_unit_year__academic_year=AcademicYearFactory(year=2019)
        )
        cls.url = reverse("tutor_edit_educational_information", args=[cls.attribution.learning_unit_year.id])
        cls.tutor.person.user.user_permissions.add(Permission.objects.get(codename='can_edit_learningunit_pedagogy'))

    def setUp(self):
        self.client.force_login(self.tutor.person.user)

        self.patcher_perm_can_edit_educational_information = mock.patch.object(BasePerm, "is_valid")
        self.mock_perm_view = self.patcher_perm_can_edit_educational_information.start()
        self.mock_perm_view.return_value = True

    def tearDown(self):
        self.patcher_perm_can_edit_educational_information.stop()

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_check_if_user_can_view_educational_information(self):
        self.mock_perm_view.return_value = False

        response = self.client.get(self.url)

        self.assertTrue(self.mock_perm_view.called)
        self.assertTemplateUsed(response, "access_denied.html")

    @mock.patch("attribution.views.manage_my_courses.edit_learning_unit_pedagogy", return_value=HttpResponse())
    def test_use_edit_learning_unit_pedagogy_method(self, mock_edit_learning_unit_pedagogy):
        self.client.get(self.url)
        self.assertTrue(mock_edit_learning_unit_pedagogy.called)

    @mock.patch("attribution.views.manage_my_courses.edit_learning_unit_pedagogy", return_value=HttpResponse())
    def test_use_edit_learning_unit_pedagogy_method(self, mock_edit_learning_unit_pedagogy):
        self.client.get(self.url)
        self.assertTrue(mock_edit_learning_unit_pedagogy.called)

    @mock.patch("attribution.views.manage_my_courses.edit_learning_unit_pedagogy", return_value=HttpResponse())
    @override_settings(YEAR_LIMIT_LUE_MODIFICATION=2018)
    def test_should_not_call_edit_learning_unit_pedagogy_method_before_2018(self, mock_edit_learning_unit_pedagogy):
        self.attribution.learning_unit_year.academic_year = AcademicYearFactory(year=2015)
        self.attribution.learning_unit_year.save()
        self.client.get(self.url)
        self.assertFalse(mock_edit_learning_unit_pedagogy.called)


class ManageMyCoursesMixin(TestCase):
    """This mixin is used in context of edition of pedagogy data for tutor"""

    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.academic_calendar = AcademicCalendarFactory(
            academic_year=cls.current_academic_year,
            data_year=cls.current_academic_year,
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
        )
        cls.academic_year_in_future = AcademicYearFactory(year=cls.current_academic_year.year + 1)
        cls.academic_calendar = OpenAcademicCalendarFactory(
            academic_year=cls.academic_year_in_future,
            data_year=cls.academic_year_in_future,
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
        )
        a_valid_entity_version = EntityVersionFactory(entity_type=FACULTY)
        cls.learning_unit_year = LearningUnitYearFactory(
            subtype=FULL,
            academic_year=cls.academic_year_in_future,
            learning_container_year__academic_year=cls.academic_year_in_future,
            learning_container_year__requirement_entity=a_valid_entity_version.entity,
            summary_locked=False
        )
        cls.tutor = _get_tutor()
        # Add attribution to course [set summary responsible]
        AttributionFactory(
            tutor=cls.tutor,
            summary_responsible=True,
            learning_unit_year=cls.learning_unit_year,
        )

    def setUp(self):
        self.client.force_login(self.tutor.person.user)


class TestManageMyCoursesTeachingMaterials(ManageMyCoursesMixin):
    def setUp(self):
        super().setUp()
        self.teaching_material = TeachingMaterialFactory(learning_unit_year=self.learning_unit_year)

    @patch('base.views.teaching_material.create_view')
    def test_call_view_create_teaching_material(self, mock_create_view):
        url = reverse('tutor_teaching_material_create', kwargs={'learning_unit_year_id': self.learning_unit_year.id})
        request = _prepare_request(url, self.tutor.person.user)

        from attribution.views.manage_my_courses import create_teaching_material
        create_teaching_material(request, learning_unit_year_id=self.learning_unit_year.pk)
        self.assertTrue(mock_create_view.called)

        mock_create_view.assert_called_once_with(request, self.learning_unit_year.pk)

    @patch('base.views.teaching_material.update_view')
    def test_call_view_update_teaching_material(self, mock_update_view):
        url = reverse('tutor_teaching_material_edit', kwargs={'learning_unit_year_id': self.learning_unit_year.id,
                                                              'teaching_material_id': self.teaching_material.id})
        request = _prepare_request(url, self.tutor.person.user)

        from attribution.views.manage_my_courses import update_teaching_material
        update_teaching_material(
            request,
            learning_unit_year_id=self.learning_unit_year.pk,
            teaching_material_id=self.teaching_material.id
        )
        self.assertTrue(mock_update_view.called)

        mock_update_view.assert_called_once_with(request, self.learning_unit_year.pk, self.teaching_material.id)

    @patch('base.views.teaching_material.delete_view')
    def test_call_view_delete_teaching_material(self, mock_delete_view):
        url = reverse('tutor_teaching_material_delete', kwargs={'learning_unit_year_id': self.learning_unit_year.id,
                                                                'teaching_material_id': self.teaching_material.id})
        request = _prepare_request(url, self.tutor.person.user)

        from attribution.views.manage_my_courses import delete_teaching_material
        delete_teaching_material(
            request,
            learning_unit_year_id=self.learning_unit_year.pk,
            teaching_material_id=self.teaching_material.id
        )
        self.assertTrue(mock_delete_view.called)

        mock_delete_view.assert_called_once_with(request, self.learning_unit_year.pk, self.teaching_material.id)


def _prepare_request(url, user):
    request_factory = RequestFactory()
    request = request_factory.get(url)
    request.user = user
    return request


def _get_tutor():
    tutor = TutorFactory()
    tutor.person.user.user_permissions.add(Permission.objects.get(codename="can_edit_learningunit_pedagogy"))
    return tutor

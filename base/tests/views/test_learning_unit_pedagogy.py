##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from io import BytesIO
from unittest import mock
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseNotAllowed
from django.http.response import HttpResponseForbidden, HttpResponseRedirect
from django.test import TestCase, RequestFactory
from django.utils.translation import ugettext_lazy as _
from openpyxl import load_workbook
from waffle.testutils import override_flag

from attribution.tests.factories.attribution import AttributionFactory
from base.business.learning_unit import CMS_LABEL_PEDAGOGY_FR_ONLY
from base.models.academic_year import current_academic_year, starting_academic_year
from base.models.enums import academic_calendar_type
from base.models.enums import entity_container_year_link_type
from base.models.enums import learning_container_year_types, organization_type
from base.models.enums.learning_unit_year_subtypes import FULL
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_calendar import EntityCalendarFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory, FacultyManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.teaching_material import TeachingMaterialFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.user import UserFactory
from base.views.learning_units.educational_information import learning_units_summary_list, \
    send_email_educational_information_needs_update
from base.views.learning_units.pedagogy.update import learning_unit_pedagogy_edit
from base.views.learning_units.search import SUMMARY_LIST
from cms.enums import entity_name
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory
from reference.tests.factories.country import CountryFactory


class LearningUnitPedagogyTestCase(TestCase):
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.previous_academic_year = \
            GenerateAcademicYear(self.current_academic_year.year-1, self.current_academic_year.year-1).academic_years[0]
        self.next_academic_year = AcademicYearFactory(year=self.current_academic_year.year + 1)
        self.organization = OrganizationFactory(type=organization_type.MAIN)
        self.country = CountryFactory()
        self.url = reverse(learning_units_summary_list)
        faculty_managers_group = Group.objects.get(name='faculty_managers')
        self.faculty_user = UserFactory()
        self.faculty_user.groups.add(faculty_managers_group)
        self.faculty_person = PersonFactory(user=self.faculty_user)

        self.an_entity = EntityFactory(country=self.country, organization=self.organization)
        PersonEntityFactory(person=self.faculty_person, entity=self.an_entity)

    def test_learning_units_summary_list_no_access(self):
        request_factory = RequestFactory()
        a_user = UserFactory()
        request = request_factory.get(self.url)
        request.user = a_user
        self.client.force_login(a_user)
        with self.assertRaises(PermissionDenied):
            learning_units_summary_list(request)

    @mock.patch('base.views.layout.render')
    def test_learning_units_summary_list_no_entity_calendar(self, mock_render):

        request_factory = RequestFactory()

        EntityVersionFactory(entity=self.an_entity)

        request = request_factory.get(self.url)
        request.user = self.faculty_user
        self._create_learning_unit_year_for_entity(self.an_entity, "LBIR1100")
        self.client.force_login(self.faculty_user)

        learning_units_summary_list(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(context['search_type'], SUMMARY_LIST)
        self.assertEqual(len(context['learning_units_with_errors']), 0)

    @mock.patch('base.views.layout.render')
    def test_learning_units_summary_list(self, mock_render):
        request_factory = RequestFactory()

        now = datetime.datetime.now()

        EntityVersionFactory(entity=self.an_entity,
                             start_date=now,
                             end_date=datetime.datetime(now.year+1, 9, 15),
                             entity_type='INSTITUTE')

        request = request_factory.get(self.url, data={'academic_year_id': starting_academic_year().id})
        request.user = self.faculty_user

        lu = self._create_learning_unit_year_for_entity(self.an_entity, "LBIR1100")
        person_lu = PersonFactory()
        tutor_lu_1 = TutorFactory(person=person_lu)
        self.attribution_lu = AttributionFactory(learning_unit_year=lu, tutor=tutor_lu_1, summary_responsible=True)
        self._create_entity_calendar(self.an_entity)
        self.client.force_login(self.faculty_user)

        learning_units_summary_list(request)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(context['search_type'], SUMMARY_LIST)
        self.assertEqual(len(context['learning_units_with_errors']), 1)
        self.assertTrue(context['is_faculty_manager'])

    def test_learning_units_summary_list_by_client(self):
        self.client.force_login(self.faculty_user)
        response = self.client.get(self.url, data={'academic_year_id': current_academic_year().id})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "learning_units.html")

    def test_learning_units_summary_list_by_client_xls(self):
        # Generate data
        now = datetime.datetime.now()
        EntityVersionFactory(entity=self.an_entity,
                             start_date=now,
                             end_date=datetime.datetime(now.year+1, 9, 15),
                             entity_type='INSTITUTE')

        luy = self._create_learning_unit_year_for_entity(self.an_entity, "LBIR1100")
        self._create_entity_calendar(self.an_entity)

        TeachingMaterialFactory(learning_unit_year=luy, title="Magic wand", mandatory=True)
        TeachingMaterialFactory(learning_unit_year=luy, title="Broomsticks", mandatory=False)

        luy_without_mandatory_teaching_material = self._create_learning_unit_year_for_entity(self.an_entity, "LBIR1101")
        TeachingMaterialFactory(learning_unit_year=luy_without_mandatory_teaching_material, title="cauldron", mandatory=False)

        # Test the view
        self.client.force_login(self.faculty_user)
        response = self.client.get(self.url, data={
            'academic_year_id': starting_academic_year().id,
            'xls_status': 'xls_teaching_material'
        })

        # OK, the server returned the xls file
        self.assertEqual(response.status_code, 200)
        wb = load_workbook(BytesIO(response.content), read_only=True)

        sheet = wb.active
        data = sheet['A1': 'F3']

        # Check the first row content
        titles = next(data)
        title_values = list(t.value for t in titles)
        self.assertEqual(title_values, [
            str(_('code')).title(),
            str(_('Title')),
            str(_('Req. Entity')).title(),
            str(_('bibliography')).title(),
            str(_('teaching materials')).title(),
            str(_('online resources')).title(),
        ])

        # Check data from the luy
        first_luy = next(data)
        first_luy_values = list(t.value for t in first_luy)
        self.assertEqual(first_luy_values, [
            luy.acronym, luy.complete_title, str(luy.requirement_entity), " ", "Magic wand", " "
        ])

        # The second luy has no mandatory teaching material
        with self.assertRaises(StopIteration):
            next(data)

    def test_learning_units_summary_list_by_client_xls_empty(self):
        # Generate data
        now = datetime.datetime.now()
        EntityVersionFactory(entity=self.an_entity,
                             start_date=now,
                             end_date=datetime.datetime(now.year+1, 9, 15),
                             entity_type='INSTITUTE')

        luy = self._create_learning_unit_year_for_entity(self.an_entity, "LBIR1100")
        self._create_entity_calendar(self.an_entity)

        TeachingMaterialFactory(learning_unit_year=luy, title="Magic wand", mandatory=False)
        TeachingMaterialFactory(learning_unit_year=luy, title="Broomsticks", mandatory=False)

        luy_without_mandatory_teaching_material = self._create_learning_unit_year_for_entity(self.an_entity, "LBIR1101")
        TeachingMaterialFactory(learning_unit_year=luy_without_mandatory_teaching_material, title="cauldron", mandatory=False)

        # Test the view
        self.client.force_login(self.faculty_user)
        response = self.client.get(self.url, data={
            'academic_year_id': starting_academic_year().id,
            'xls_status': 'xls_teaching_material'
        })

        # OK, the server will stay in the page
        self.assertEqual(response.status_code, 200)

        # A warning message should be generated
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), _("the list to generate is empty.").capitalize())

    def _create_entity_calendar(self, an_entity):
        an_academic_calendar = AcademicCalendarFactory(academic_year=self.previous_academic_year,
                                                       start_date=self.previous_academic_year.start_date,
                                                       end_date=self.previous_academic_year.end_date,
                                                       reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)
        EntityCalendarFactory(entity=an_entity, academic_calendar=an_academic_calendar,
                              start_date=an_academic_calendar.start_date,
                              end_date=an_academic_calendar.end_date)

    def _create_learning_unit_year_for_entity(self, an_entity, acronym):
        l_container_yr = LearningContainerYearFactory(acronym=acronym,
                                                      academic_year=self.current_academic_year,
                                                      container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr,
                                   entity=an_entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        return LearningUnitYearFactory(acronym=acronym,
                                       learning_container_year=l_container_yr,
                                       academic_year=self.current_academic_year)

    @override_flag('educational_information_mailing', active=True)
    def test_send_email_educational_information_needs_update_no_access(self):
        request_factory = RequestFactory()
        a_user = UserFactory()
        request = request_factory.get(self.url)
        request.user = a_user
        self.client.force_login(a_user)
        with self.assertRaises(PermissionDenied):
            send_email_educational_information_needs_update(request)

    def test_learning_unit_pedagogy_edit(self):
        luy = self._create_learning_unit_year_for_entity(self.an_entity, "LBIR1100")
        edit_url = reverse(learning_unit_pedagogy_edit, kwargs={'learning_unit_year_id': luy.id})

        text_label_bibliography = TextLabelFactory(
            entity=entity_name.LEARNING_UNIT_YEAR,
            label='bibliography'
        )
        TranslatedTextFactory(
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=luy.id,
            language='fr-be',
            text_label=text_label_bibliography,
            text='Some random text'
        )

        self.client.force_login(self.faculty_user)
        response = self.client.get(edit_url, data={'label': 'bibliography', 'language': 'fr-be'})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'learning_unit/pedagogy_edit.html')
        self.assertTemplateUsed(response, 'learning_unit/blocks/modal/modal_pedagogy_edit.html')
        self.assertEqual(response.context["cms_label_pedagogy_fr_only"], CMS_LABEL_PEDAGOGY_FR_ONLY)
        self.assertEqual(response.context["label_name"], 'bibliography')


class LearningUnitPedagogySummaryLockedTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.faculty_person = FacultyManagerFactory()
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.current_academic_year,
            learning_container_year__academic_year=cls.current_academic_year,
            subtype=FULL
        )
        cls.url = reverse('learning_unit_pedagogy_toggle_summary_locked',
                          kwargs={'learning_unit_year_id': cls.learning_unit_year.pk})

    def setUp(self):
        self.client.force_login(self.faculty_person.user)

    def test_toggle_summary_locked_case_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_toggle_summary_locked_case_method_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    @patch('base.business.learning_units.perms.can_edit_summary_locked_field')
    def test_toggle_summary_locked_case_cannot_edit_summary_locked(self, mock_can_edit_summary_locked):
        mock_can_edit_summary_locked.return_value = False
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @patch('base.views.learning_units.pedagogy.update.display_success_messages')
    @patch('base.business.learning_units.perms.can_edit_summary_locked_field')
    def test_toggle_summary_locked_case_success(self, mock_can_edit_summary_locked, mock_diplay_success_message):
        mock_can_edit_summary_locked.return_value = True
        self.learning_unit_year.summary_locked = True
        self.learning_unit_year.save()

        response = self.client.post(self.url, follow=False)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        self.assertTrue(mock_diplay_success_message.called)
        expected_redirection = reverse("learning_unit_pedagogy",
                                       kwargs={'learning_unit_year_id': self.learning_unit_year.pk})
        self.assertRedirects(response, expected_redirection)
        self.learning_unit_year.refresh_from_db()
        self.assertFalse(self.learning_unit_year.summary_locked)

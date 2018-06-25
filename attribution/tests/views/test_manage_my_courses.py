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
from unittest import mock

from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse

from attribution.tests.factories.attribution import AttributionFactory
from attribution.views.manage_my_courses import list_my_attributions_summary_editable, view_educational_information
from base.business.learning_units.perms import can_user_view_educational_information
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyForm
from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory


class ManageMyCoursesViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.user = cls.person.user
        cls.tutor = TutorFactory(person=cls.person)

        cls.attribution = AttributionFactory(tutor=cls.tutor,
                                             summary_responsible=True,
                                             learning_unit_year__summary_locked=False)
        cls.academic_calendar = AcademicCalendarFactory(academic_year=create_current_academic_year(),
                                                        reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)
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
        self.assertEquals(response.status_code, HttpResponseNotFound.status_code)

    @mock.patch("attribution.views.manage_my_courses.find_learning_unit_years_summary_editable")
    def test_list_my_attributions_summary_editable(self, mock_find_luys_summary_editable):
        expected_luys_summary_editable = [self.attribution.learning_unit_year]
        mock_find_luys_summary_editable.return_value = expected_luys_summary_editable

        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "manage_my_courses/list_my_courses_summary_editable.html")
        self.assertTrue(mock_find_luys_summary_editable.called)

        context = response.context
        self.assertCountEqual(context['learning_unit_years_summary_editable'], expected_luys_summary_editable)
        self.assertDictEqual(context['submission_dates'], model_to_dict(self.academic_calendar,
                                                                        fields=("start_date", "end_date")))


class TestViewEducationalInformation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tutor = TutorFactory()
        cls.attribution = AttributionFactory(tutor=cls.tutor, summary_responsible=True)
        cls.url = reverse(view_educational_information, args=[cls.attribution.learning_unit_year.id])

    def setUp(self):
        self.client.force_login(self.tutor.person.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    @mock.patch("attribution.views.perms.can_user_view_educational_information", return_value=False)
    def test_check_if_user_can_view_educational_information(self, mock_perm):
        response = self.client.get(self.url)
        self.assertTrue(mock_perm.called)
        self.assertTemplateUsed(response, "access_denied.html")

    @mock.patch("attribution.views.manage_my_courses.can_user_edit_educational_information",
                side_effect=lambda usr, luy_id: False)
    @mock.patch("attribution.views.manage_my_courses.find_educational_information_submission_dates_of_learning_unit_year",
                return_value={})
    def test_template_used(self, mock_find_submission_dates, mock_can_edit):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "manage_my_courses/educational_information.html")
        self.assertTrue(mock_can_edit.called)
        self.assertTrue(mock_find_submission_dates.called)

        context = response.context
        self.assertEqual(context["learning_unit_year"], self.attribution.learning_unit_year)
        self.assertTrue(context["cms_labels_translated"])
        self.assertIsInstance(context["form_french"], LearningUnitPedagogyForm)
        self.assertIsInstance(context["form_english"], LearningUnitPedagogyForm)
        self.assertFalse(context["can_edit_information"])
        self.assertFalse(context["submission_dates"])


class TestManageEducationalInformation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tutor = TutorFactory()
        cls.attribution = AttributionFactory(tutor=cls.tutor, summary_responsible=True)
        cls.url = reverse("tutor_edit_educational_information", args=[cls.attribution.learning_unit_year.id])

    def setUp(self):
        self.client.force_login(self.tutor.person.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    @mock.patch("attribution.views.perms.can_user_edit_educational_information",
                side_effect=lambda req, luy: False)
    def test_check_if_user_can_view_educational_information(self, mock_perm):
        response = self.client.get(self.url)
        self.assertTrue(mock_perm.called)
        self.assertTemplateUsed(response, "access_denied.html")

    @mock.patch("attribution.views.manage_my_courses.edit_learning_unit_pedagogy", return_value=HttpResponse())
    @mock.patch("attribution.views.perms.can_user_edit_educational_information", return_value=True)
    def test_use_edit_learning_unit_pedagogy_method(self, mock_can_edit, mock_edit_learning_unit_pedagogy):
        self.client.get(self.url)
        self.assertTrue(mock_edit_learning_unit_pedagogy.called)
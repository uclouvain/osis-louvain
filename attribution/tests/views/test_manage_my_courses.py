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
import datetime

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from base.forms.learning_unit_pedagogy import LearningUnitPedagogyForm
from base.models.tutor import Tutor
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory

from attribution.tests.factories.attribution import AttributionFactory
from attribution.views.manage_my_courses import list_my_attributions_summary_editable


HTTP_NOT_FOUND = 404


class ManageMyCoursesViewTestCase(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.user = self.person.user
        self.tutor = TutorFactory(person=self.person)
        self.academic_year = AcademicYearFactory(year=datetime.date.today().year,
                                                 start_date=datetime.date.today())

        self.learning_unit_years = [LearningUnitYearFactory(summary_editable=True)
                                    for i in range(4)]
        self.attributions = [AttributionFactory(tutor=self.tutor,
                                                summary_responsible=True,
                                                learning_unit_year=self.learning_unit_years[i])
                             for i in range(4)]

    def test_list_my_attributions_summary_editable_user_not_logged(self):
        url = reverse(list_my_attributions_summary_editable)
        self.client.logout()
        response = self.client.get(url)
        self.assertRedirects(response, '/login/?next={}'.format(url))

    def test_list_my_attributions_summary_editable_user_not_tutor(self):
        tutors = Tutor.objects.filter(person__user=self.user)
        tutors.delete()

        self.client.force_login(self.user)
        url = reverse(list_my_attributions_summary_editable)
        response = self.client.get(url, follow=True)
        self.assertEquals(response.status_code, HTTP_NOT_FOUND)

    def test_list_my_attributions_summary_editable(self):
        self.client.force_login(self.user)
        url = reverse(list_my_attributions_summary_editable)
        response = self.client.get(url)
        self.assertTemplateUsed(response, "manage_my_courses/list_my_courses_summary_editable.html")

        context = response.context[-1]
        self.assertCountEqual(context['learning_unit_years_summary_editable'], self.learning_unit_years)


    def test_list_my_attributions_summary_editable_false_for_some(self):
        self.client.force_login(self.user)

        self.learning_unit_years[0].summary_editable = False
        self.learning_unit_years[0].save()
        self.learning_unit_years[2].summary_editable = False
        self.learning_unit_years[2].save()

        url = reverse(list_my_attributions_summary_editable)
        response = self.client.get(url)

        self.assertTemplateUsed(response, "manage_my_courses/list_my_courses_summary_editable.html")

        context = response.context[-1]
        self.assertCountEqual(context['learning_unit_years_summary_editable'],
                              [self.learning_unit_years[1], self.learning_unit_years[3]])

    def test_list_my_attributions_summary_responsible_false_for_some(self):
        self.client.force_login(self.user)

        self.attributions[0].summary_responsible = False
        self.attributions[0].save()
        self.attributions[2].summary_responsible = False
        self.attributions[2].save()

        url = reverse(list_my_attributions_summary_editable)
        response = self.client.get(url)
        self.assertTemplateUsed(response, "manage_my_courses/list_my_courses_summary_editable.html")

        context = response.context[-1]
        self.assertCountEqual(context['learning_unit_years_summary_editable'],
                              [self.learning_unit_years[1], self.learning_unit_years[3]])

    def test_list_my_attributions_summary_responsible_and_summary_editable_false_for_some(self):
        self.client.force_login(self.user)

        self.attributions[0].summary_responsible = False
        self.attributions[0].save()
        self.attributions[2].summary_responsible = False
        self.attributions[2].save()

        self.attributions[0].summary_responsible = False
        self.attributions[0].save()
        self.attributions[2].summary_responsible = False
        self.attributions[2].save()

        url = reverse(list_my_attributions_summary_editable)
        response = self.client.get(url)
        self.assertTemplateUsed(response, "manage_my_courses/list_my_courses_summary_editable.html")

        context = response.context[-1]
        self.assertCountEqual(context['learning_unit_years_summary_editable'],
                              [self.learning_unit_years[1], self.learning_unit_years[3]])

class TestViewEducationalInformation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tutor = TutorFactory()
        cls.attribution = AttributionFactory(tutor=cls.tutor, summary_responsible=True)
        cls.url = reverse("view_educational_information", args=[cls.attribution.learning_unit_year.id])

    def setUp(self):
        self.client.force_login(self.tutor.person.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    @mock.patch("attribution.business.perms.can_user_edit_educational_information",
                side_effect=lambda req, luy: False)
    def test_check_if_user_can_view_educational_information(self, mock_perm):
        response = self.client.get(self.url)
        self.assertTrue(mock_perm.called)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_template_used(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "manage_my_courses/educational_information.html")

        context = response.context
        self.assertEqual(context["learning_unit_year"], self.attribution.learning_unit_year)
        self.assertTrue(context["cms_labels_translated"])
        self.assertIsInstance(context["form_french"], LearningUnitPedagogyForm)
        self.assertIsInstance(context["form_english"], LearningUnitPedagogyForm)


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

    @mock.patch("attribution.business.perms.can_user_edit_educational_information",
                side_effect=lambda req, luy: False)
    def test_check_if_user_can_view_educational_information(self, mock_perm):
        response = self.client.get(self.url)
        self.assertTrue(mock_perm.called)
        self.assertTemplateUsed(response, "access_denied.html")

    @mock.patch("base.views.learning_unit.edit_learning_unit_pedagogy",
                side_effect=lambda req, luy_id, url: HttpResponse())
    def test_use_edit_learning_unit_pedagogy_method(self, mock_edit_learning_unit_pedagogy):
        self.client.get(self.url)
        self.assertTrue(mock_edit_learning_unit_pedagogy.called)
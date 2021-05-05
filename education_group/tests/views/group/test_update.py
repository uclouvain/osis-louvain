##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from typing import List
from unittest import mock

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.person import PersonFactory
from education_group.ddd.domain.exception import GroupNotFoundException
from education_group.ddd.domain.group import GroupIdentity
from education_group.forms.group import GroupUpdateForm
from education_group.tests.ddd.factories.group import GroupFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestUpdateGroupGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = GroupFactory()
        cls.program_tree = ProgramTreeFactory()

        cls.group.entity_identity = GroupIdentity(year=2018, code='LBIR100M')
        cls.central_manager = CentralManagerFactory()
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT.name,
            data_year__year=cls.group.year
        )
        cls.url = reverse('group_update', kwargs={'year': cls.group.year, 'code': cls.group.code})

    def setUp(self) -> None:
        self.get_group_patcher = mock.patch(
            "education_group.views.group.update.get_group_service.get_group",
            return_value=self.group
        )
        self.mocked_get_group = self.get_group_patcher.start()
        self.addCleanup(self.get_group_patcher.stop)

        self.client.force_login(self.central_manager.person.user)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch('education_group.views.group.update.get_group_service.get_group', side_effect=GroupNotFoundException)
    def test_assert_404_when_group_not_found(self, mock_get_group):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "education_group_app/group/upsert/update.html")

    def test_assert_context(self):
        response = self.client.get(self.url)

        self.assertIsInstance(response.context['group_form'], GroupUpdateForm)
        self.assertIsInstance(response.context['tabs'], List)
        self.assertIsInstance(response.context['cancel_url'], str)

    def test_assert_contains_identification(self):
        response = self.client.get(self.url)

        self.assertListEqual(
            response.context['tabs'],
            [{
                "id": "identification",
                "text": _("Identification"),
                "active": True,
                "display": True,
                "include_html": "education_group_app/group/upsert/identification_form.html"
            }]
        )

    def test_assert_cancel_url_computed(self):
        response = self.client.get(self.url)

        expected_url = reverse('element_identification', kwargs={'year': self.group.year, 'code': self.group.code})
        self.assertEqual(response.context['cancel_url'], expected_url)

    def test_assert_cancel_url_keep_path_queryparam(self):
        url_with_path = self.url + "?path=25656565|56565"

        response = self.client.get(url_with_path)
        expected_url = reverse('element_identification', kwargs={'year': self.group.year, 'code': self.group.code}) + \
            "?path=25656565|56565"
        self.assertEqual(response.context['cancel_url'], expected_url)

    def test_assert_group_form_initial_computed(self):
        response = self.client.get(self.url)

        initials = response.context['group_form'].initial
        self.assertEqual(initials['code'], self.group.code)
        self.assertEqual(initials['abbreviated_title'], self.group.abbreviated_title)
        self.assertEqual(initials['title_fr'], self.group.titles.title_fr)
        self.assertEqual(initials['title_en'], self.group.titles.title_en)
        self.assertEqual(initials['credits'], self.group.credits)
        self.assertEqual(initials['constraint_type'], self.group.content_constraint.type.name)
        self.assertEqual(initials['min_constraint'], self.group.content_constraint.minimum)
        self.assertEqual(initials['max_constraint'], self.group.content_constraint.maximum)
        self.assertEqual(initials['remark_fr'], self.group.remark.text_fr)
        self.assertEqual(initials['remark_en'], self.group.remark.text_en)


class TestUpdateGroupPostMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = GroupFactory()
        cls.program_tree = ProgramTreeFactory()

        cls.group.entity_identity = GroupIdentity(year=2018, code='LBIR100M')
        cls.central_manager = CentralManagerFactory()
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT.name,
            data_year__year=cls.group.year
        )
        cls.url = reverse('group_update', kwargs={'year': cls.group.year, 'code': cls.group.code})

    def setUp(self) -> None:
        self.get_group_patcher = mock.patch(
            "education_group.views.group.update.get_group_service.get_group",
            return_value=self.group
        )
        self.mocked_get_group = self.get_group_patcher.start()
        self.addCleanup(self.get_group_patcher.stop)

        self.update_group_patcher = mock.patch(
            "education_group.views.group.update.update_group_service.update_group",
            return_value=self.group
        )
        self.mocked_update_group = self.update_group_patcher.start()
        self.addCleanup(self.update_group_patcher.stop)

        self.client.force_login(self.central_manager.person.user)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch('education_group.views.group.update.get_group_service.get_group', side_effect=GroupNotFoundException)
    def test_assert_404_when_group_not_found(self, mock_get_group):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    @mock.patch('education_group.views.group.update.GroupUpdateForm')
    def test_case_all_forms_valid_assert_redirection(self, mock_group_form):
        mock_group_form.return_value.is_valid.return_value = True

        expected_redirect = reverse(
            'element_identification', kwargs={'code': self.group.code, 'year': self.group.year}
        )
        response = self.client.post(self.url, data={})
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)

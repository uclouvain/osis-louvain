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
from unittest import mock

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.tests.factories.person import PersonFactory
from education_group.ddd.domain.exception import GroupNotFoundException
from education_group.ddd.domain.group import GroupIdentity
from education_group.ddd.factories.group import GroupFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.group_year import GroupYearFactory as GroupYearDBFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestDeleteGroupGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = GroupFactory()
        cls.program_tree = ProgramTreeFactory()

        cls.group.entity_identity = GroupIdentity(year=2018, code='LBIR100M')
        cls.central_manager = CentralManagerFactory()
        cls.url = reverse('group_delete', kwargs={'year': cls.group.year, 'code': cls.group.code})

        cls.group_year_db = GroupYearDBFactory(
            management_entity=cls.central_manager.entity,
            partial_acronym=cls.group.code,
            academic_year__year=cls.group.year
        )

    def setUp(self) -> None:
        self.get_group_patcher = mock.patch(
            "education_group.views.group.delete.get_group_service.get_group",
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

    @mock.patch('education_group.views.group.delete.get_group_service.get_group', side_effect=GroupNotFoundException)
    def test_assert_404_when_group_not_found(self, mock_get_group):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "education_group_app/group/delete_inner.html")

    def test_assert_context(self):
        response = self.client.get(self.url)

        expected_confirmation_msg = _("Are you sure you want to delete %(code)s - %(title)s ?") % {
            'code': self.group.code,
            'title': self.group.titles.title_fr
        }
        self.assertEqual(
            response.context['confirmation_message'],
            expected_confirmation_msg
        )


class TestDeleteGroupPostMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = GroupFactory()
        cls.program_tree = ProgramTreeFactory()

        cls.group.entity_identity = GroupIdentity(year=2018, code='LBIR100M')
        cls.central_manager = CentralManagerFactory()
        cls.url = reverse('group_delete', kwargs={'year': cls.group.year, 'code': cls.group.code})

        cls.group_year_db = GroupYearDBFactory(
            management_entity=cls.central_manager.entity,
            partial_acronym=cls.group.code,
            academic_year__year=cls.group.year
        )

    def setUp(self) -> None:
        self.get_group_patcher = mock.patch(
            "education_group.views.group.delete.get_group_service.get_group",
            return_value=self.group
        )
        self.mocked_get_group = self.get_group_patcher.start()
        self.addCleanup(self.get_group_patcher.stop)

        self.delete_all_pgrm_tree_patcher = mock.patch(
            "education_group.views.group.delete.delete_all_program_tree_service.delete_all_program_tree",
            return_value=self.group
        )
        self.mocked_delete_all_pgrm_tree = self.delete_all_pgrm_tree_patcher.start()
        self.addCleanup(self.delete_all_pgrm_tree_patcher.stop)

        self.client.force_login(self.central_manager.person.user)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_ensure_post_call_delete_all_group_service(self):
        response = self.client.post(self.url)

        self.assertTrue(self.mocked_delete_all_pgrm_tree.called)
        self.assertRedirects(response, reverse('version_program'), fetch_redirect_response=False)

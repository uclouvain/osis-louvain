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

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.person import PersonFactory
from education_group.ddd.domain.exception import MiniTrainingNotFoundException, MiniTrainingHaveLinkWithEPC
from education_group.templatetags.academic_year_display import display_as_academic_year
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.mini_training import MiniTrainingFactory
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity, NOT_A_TRANSITION
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory as \
    StandardEducationGroupVersionDbFactory


class TestDeleteMiniTrainingGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.mini_training = MiniTrainingFactory()
        cls.root_node = NodeGroupYearFactory(year=cls.mini_training.year)
        cls.program_tree_version = ProgramTreeVersionFactory(
            entity_id=ProgramTreeVersionIdentity(
                offer_acronym=cls.mini_training.acronym,
                year=cls.mini_training.year,
                version_name="",
                transition_name=NOT_A_TRANSITION
            ),
            tree=ProgramTreeFactory(root_node=cls.root_node)
        )

        cls.central_manager = CentralManagerFactory()
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT.name,
            data_year__year=cls.root_node.year
        )
        cls.url = reverse('mini_training_delete', kwargs={'year': cls.root_node.year, 'code': cls.root_node.code})

        # Need for permission checking
        cls.education_group_version_db = StandardEducationGroupVersionDbFactory(
            offer__management_entity=cls.central_manager.entity,
            offer__academic_year__year=cls.mini_training.year,
            offer__acronym=cls.mini_training.acronym,

            root_group__partial_acronym=cls.root_node.code,
            root_group__academic_year__year=cls.root_node.year,
            root_group__management_entity=cls.central_manager.entity,
        )

    def setUp(self) -> None:
        self.get_mini_training_patcher = mock.patch(
            "education_group.views.mini_training.delete.get_mini_training_service.get_mini_training",
            return_value=self.mini_training
        )
        self.mocked_get_training = self.get_mini_training_patcher.start()
        self.addCleanup(self.get_mini_training_patcher.stop)

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

    @mock.patch('education_group.views.mini_training.delete.get_mini_training_service.get_mini_training',
                side_effect=MiniTrainingNotFoundException)
    def test_assert_404_when_mini_training_not_found(self, mock_get_training):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    @mock.patch('program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository.get')
    def test_assert_template_used(self, mock_repo):
        mock_repo.return_value = self.program_tree_version
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "education_group_app/mini_training/delete_inner.html")

    @mock.patch('program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository.get')
    def test_assert_context(self, mock_repo):
        mock_repo.return_value = self.program_tree_version
        response = self.client.get(self.url)

        expected_confirmation_msg = _("Are you sure you want to delete %(object)s ?") % {
            'object': "{} - {}".format(self.root_node.title, self.root_node.offer_title_fr)
        }
        self.assertEqual(
            response.context['confirmation_message'],
            expected_confirmation_msg
        )


class TestDeleteMiniTrainingPostMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.mini_training = MiniTrainingFactory()
        cls.root_node = NodeGroupYearFactory(year=cls.mini_training.year)
        cls.program_tree_version = ProgramTreeVersionFactory(
            entity_id=ProgramTreeVersionIdentity(
                offer_acronym=cls.mini_training.acronym,
                year=cls.mini_training.year,
                version_name="",
                transition_name=NOT_A_TRANSITION
            ),
            tree=ProgramTreeFactory(root_node=cls.root_node)
        )

        cls.central_manager = CentralManagerFactory()
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT.name,
            data_year__year=cls.root_node.year
        )
        cls.url = reverse('mini_training_delete', kwargs={'year': cls.root_node.year, 'code': cls.root_node.code})

        # Need for permission checking
        cls.education_group_version_db = StandardEducationGroupVersionDbFactory(
            offer__management_entity=cls.central_manager.entity,
            offer__academic_year__year=cls.mini_training.year,
            offer__acronym=cls.mini_training.acronym,

            root_group__partial_acronym=cls.root_node.code,
            root_group__academic_year__year=cls.root_node.year,
            root_group__management_entity=cls.central_manager.entity,
        )

    def setUp(self) -> None:
        self.get_mini_training_patcher = mock.patch(
            "education_group.views.mini_training.delete.get_mini_training_service.get_mini_training",
            return_value=self.mini_training
        )
        self.mocked_get_training = self.get_mini_training_patcher.start()
        self.addCleanup(self.get_mini_training_patcher.stop)

        self.delete_all_standard_versions_patcher = mock.patch(
            "education_group.views.mini_training.delete.delete_all_mini_training_versions_service."
            "delete_permanently_mini_training_standard_version",
            return_value=[self.program_tree_version.entity_id]
        )
        self.mocked_delete_all_standard_versions = self.delete_all_standard_versions_patcher.start()
        self.addCleanup(self.delete_all_standard_versions_patcher.stop)

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

    def test_ensure_post_call_delete_all_standard_versions_service(self):
        response = self.client.post(self.url)

        self.assertTrue(self.mocked_delete_all_standard_versions.called)
        self.assertRedirects(response, reverse('version_program'), fetch_redirect_response=False)

    def test_ensure_post_call_show_training_have_link_exception_when_raised(self):
        self.mocked_delete_all_standard_versions.side_effect = MiniTrainingHaveLinkWithEPC(
            abbreviated_title=self.mini_training.acronym,
            year=self.mini_training.year
        )

        response = self.client.post(self.url)

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            _("The mini-training {abbreviated_title} ({academic_year}) have links in EPC application").format(
                abbreviated_title=self.mini_training.acronym,
                academic_year=display_as_academic_year(self.mini_training.year)
            )
        )

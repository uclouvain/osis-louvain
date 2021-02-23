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

from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.person import PersonFactory
from education_group.ddd.domain.exception import TrainingNotFoundException, TrainingHaveLinkWithEPC
from education_group.templatetags.academic_year_display import display_as_academic_year
from education_group.tests.ddd.factories.training import TrainingFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity, NOT_A_TRANSITION
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory as \
    StandardEducationGroupVersionDbFactory


class TestDeleteTrainingGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.training = TrainingFactory()
        cls.root_node = NodeGroupYearFactory(year=cls.training.year)
        cls.program_tree_version = ProgramTreeVersionFactory(
            entity_id=ProgramTreeVersionIdentity(
                offer_acronym=cls.training.acronym,
                year=cls.training.year,
                version_name="",
                transition_name=NOT_A_TRANSITION
            ),
            tree=ProgramTreeFactory(root_node=cls.root_node)
        )

        cls.central_manager = CentralManagerFactory()
        OpenAcademicCalendarFactory(
            reference=academic_calendar_type.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT,
            data_year__year=cls.root_node.year
        )
        cls.url = reverse('training_delete', kwargs={'year': cls.root_node.year, 'code': cls.root_node.code})

        # Need for permission checking
        cls.education_group_version_db = StandardEducationGroupVersionDbFactory(
            offer__management_entity=cls.central_manager.entity,
            offer__academic_year__year=cls.training.year,
            offer__acronym=cls.training.acronym,

            root_group__partial_acronym=cls.root_node.code,
            root_group__academic_year__year=cls.root_node.year,
            root_group__management_entity=cls.central_manager.entity,
        )

    def setUp(self) -> None:
        self.get_training_patcher = mock.patch(
            "education_group.views.training.delete.get_training_service.get_training",
            return_value=self.training
        )
        self.mocked_get_training = self.get_training_patcher.start()
        self.addCleanup(self.get_training_patcher.stop)

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

    @mock.patch('education_group.views.training.delete.get_training_service.get_training',
                side_effect=TrainingNotFoundException)
    def test_assert_404_when_group_not_found(self, mock_get_training):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    @mock.patch('program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository.get')
    def test_assert_template_used(self, mock_repo):
        mock_repo.return_value = self.program_tree_version
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "education_group_app/training/delete_inner.html")

    @mock.patch('program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository.get')
    def test_assert_context(self, mock_repo):
        mock_repo.return_value = self.program_tree_version
        response = self.client.get(self.url)

        expected_confirmation_msg = \
            _("Are you sure you want to delete %(object)s ?") % {
                'object': "{} - {}".format(self.root_node.title, self.root_node.offer_title_fr)
            }
        self.assertEqual(
            response.context['confirmation_message'],
            expected_confirmation_msg
        )


class TestDeleteTrainingPostMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.training = TrainingFactory(entity_identity__year=2025)
        cls.root_node = NodeGroupYearFactory(year=cls.training.year)
        cls.program_tree_version = ProgramTreeVersionFactory(
            entity_id=ProgramTreeVersionIdentity(
                offer_acronym=cls.training.acronym,
                year=cls.training.year,
                version_name="",
                transition_name=NOT_A_TRANSITION
            ),
            tree=ProgramTreeFactory(root_node=cls.root_node)
        )

        cls.central_manager = CentralManagerFactory()
        OpenAcademicCalendarFactory(
            reference=academic_calendar_type.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT,
            data_year__year=cls.root_node.year
        )

        cls.url = reverse('training_delete', kwargs={'year': cls.root_node.year, 'code': cls.root_node.code})

        # Need for permission checking
        cls.education_group_version_db = StandardEducationGroupVersionDbFactory(
            offer__management_entity=cls.central_manager.entity,
            offer__academic_year__year=cls.training.year,
            offer__acronym=cls.training.acronym,

            root_group__partial_acronym=cls.root_node.code,
            root_group__academic_year__year=cls.root_node.year,
            root_group__management_entity=cls.central_manager.entity,
        )

    def setUp(self) -> None:
        self.get_training_patcher = mock.patch(
            "education_group.views.training.delete.get_training_service.get_training",
            return_value=self.training
        )
        self.mocked_get_training = self.get_training_patcher.start()
        self.addCleanup(self.get_training_patcher.stop)

        self.delete_all_standard_versions_patcher = mock.patch(
            "education_group.views.training.delete.delete_all_standard_versions_service"
            ".delete_permanently_training_standard_version",
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
        self.mocked_delete_all_standard_versions.side_effect = TrainingHaveLinkWithEPC(
            acronym=self.training.acronym,
            year=self.training.year
        )

        response = self.client.post(self.url)

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            _("The training {acronym} ({academic_year}) have links in EPC application").format(
                acronym=self.training.acronym,
                academic_year=display_as_academic_year(self.training.year)
            )
        )

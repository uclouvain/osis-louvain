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
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.group_year import GroupYearFactory as GroupYearDBFactory
from program_management.ddd.domain.exception import ProgramTreeVersionNotFoundException
from program_management.ddd.domain.node import NodeIdentity
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionIdentityFactory,  \
    ProgramTreeVersionFactory, StandardProgramTreeVersionFactory, SpecificProgramTreeVersionFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory


class TestDeleteVersionGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tree_version_identity = ProgramTreeVersionIdentityFactory(year=2020)

        cls.node_identity = NodeIdentity(code='LBIR111M', year=cls.tree_version_identity.year)

        cls.central_manager = CentralManagerFactory()
        cls.url = reverse(
            'delete_permanently_tree_version',
            kwargs={'year': cls.tree_version_identity.year, 'code': cls.node_identity.code}
        )

        cls.group_year_db = GroupYearDBFactory(
            management_entity=cls.central_manager.entity,
            partial_acronym=cls.node_identity.code,
            academic_year__year=cls.node_identity.year
        )
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT.name,
            data_year=cls.group_year_db.academic_year
        )

    def setUp(self) -> None:
        self.__mock_node_identity()
        self.__mock_tree_version_identity()

        self.client.force_login(self.central_manager.person.user)

    def __mock_node_identity(self):
        self.node_identity_patcher = mock.patch(
            "program_management.views.tree_version.delete.TreeVersionDeleteView.node_identity",
            new_callable=mock.PropertyMock,
            return_value=self.node_identity,
        )
        self.mocked_node_identity = self.node_identity_patcher.start()
        self.addCleanup(self.node_identity_patcher.stop)

    def __mock_tree_version_identity(self):
        self.tree_version_identity_patcher = mock.patch(
            "program_management.views.tree_version.delete.TreeVersionDeleteView.tree_version_identity",
            new_callable=mock.PropertyMock,
            return_value=self.tree_version_identity,
        )
        self.mocked_tree_version_identity = self.tree_version_identity_patcher.start()
        self.addCleanup(self.tree_version_identity_patcher.stop)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch(
        'program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository.get',
        side_effect=ProgramTreeVersionNotFoundException
    )
    def test_assert_404_when_group_not_found(self, mock_identity):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    @mock.patch('program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository.get')
    def test_assert_template_used(self, mock_repo):
        program_tree_version = ProgramTreeVersionFactory()
        mock_repo.return_value = program_tree_version
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "tree_version/delete_inner.html")

    @mock.patch('program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository.get')
    def test_assert_context_confirmation_message(self, mock_repo):
        program_tree_version = StandardProgramTreeVersionFactory(tree__root_node__offer_title_fr='Titre fr')
        mock_repo.return_value = program_tree_version
        response = self.client.get(self.url)

        expected_confirmation_msg = \
            _("Are you sure you want to delete %(object)s ?") % {
                'object': "{} - {}".format(program_tree_version.tree.root_node.title, 'Titre fr')
            }
        self.assertEqual(
            response.context['confirmation_message'],
            expected_confirmation_msg
        )

    @mock.patch('program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository.get')
    def test_assert_context_confirmation_message_version_label_and_title(self, mock_repo):
        root_node = NodeGroupYearFactory(offer_title_fr='Titre fr', version_name='CEMS', version_title_fr='CEMS title')
        program_tree_version = SpecificProgramTreeVersionFactory(tree__root_node=root_node,
                                                                 title_fr='Version title')
        mock_repo.return_value = program_tree_version

        url_specific_version = reverse(
            'delete_permanently_tree_version',
            kwargs={'year': program_tree_version.tree.root_node.year, 'code': program_tree_version.tree.root_node.code}
        )

        response = self.client.get(url_specific_version)

        expected_confirmation_msg = \
            _("Are you sure you want to delete %(object)s ?") % {
                'object': "{}{}{}".format(program_tree_version.tree.root_node.title,
                                          "[" + program_tree_version.tree.root_node.version_name + "]",
                                          " - Titre fr [CEMS title]"
                                          )
            }

        self.assertEqual(
            response.context['confirmation_message'],
            expected_confirmation_msg
        )


class TestDeleteTreeVersionPostMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tree_version_identity = ProgramTreeVersionIdentityFactory(year=2020)

        cls.node_identity = NodeIdentity(code='LBIR111M', year=cls.tree_version_identity.year)

        cls.central_manager = CentralManagerFactory()
        cls.url = reverse(
            'delete_permanently_tree_version',
            kwargs={'year': cls.tree_version_identity.year, 'code': cls.node_identity.code}
        )

        cls.group_year_db = GroupYearDBFactory(
            management_entity=cls.central_manager.entity,
            partial_acronym=cls.node_identity.code,
            academic_year__year=cls.node_identity.year
        )
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT.name,
            data_year=cls.group_year_db.academic_year
        )

    def setUp(self) -> None:
        self.__mock_node_identity()
        self.__mock_tree_version_identity()

        self.client.force_login(self.central_manager.person.user)

    def __mock_node_identity(self):
        self.node_identity_patcher = mock.patch(
            "program_management.views.tree_version.delete.TreeVersionDeleteView.node_identity",
            new_callable=mock.PropertyMock,
            return_value=self.node_identity,
        )
        self.mocked_node_identity = self.node_identity_patcher.start()
        self.addCleanup(self.node_identity_patcher.stop)

    def __mock_tree_version_identity(self):
        self.tree_version_identity_patcher = mock.patch(
            "program_management.views.tree_version.delete.TreeVersionDeleteView.tree_version_identity",
            new_callable=mock.PropertyMock,
            return_value=self.tree_version_identity,
        )
        self.mocked_tree_version_identity = self.tree_version_identity_patcher.start()
        self.addCleanup(self.tree_version_identity_patcher.stop)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch(
        "program_management.ddd.service.write.delete_all_specific_versions_service.delete_permanently_tree_version"
    )
    def test_ensure_post_call_delete_all_group_service(self, mock_service):
        response = self.client.post(self.url)

        self.assertTrue(mock_service.called)
        self.assertRedirects(response, reverse('version_program'), fetch_redirect_response=False)

# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import mock
from django.test import TestCase

from base.models.enums import education_group_types, link_type
from program_management.ddd import command
from program_management.ddd.service.read import get_default_link_type_service
from program_management.tests.ddd.factories.node import NodeGroupYearFactory


class TestGetDefaultLinkType(TestCase):
    def setUp(self) -> None:
        self.mock_get_node_identity = self._mock_get_node_identity()
        self.mock_node_repository = self._mock_node_repository()

    def _mock_get_node_identity(self) -> mock.Mock:
        get_node_identity_patcher = mock.patch(
            "program_management.ddd.service.read.node_identity_service.get_node_identity_from_element_id"
        )
        mock_get_node_identity = get_node_identity_patcher.start()
        self.addCleanup(get_node_identity_patcher.stop)
        return mock_get_node_identity

    def _mock_node_repository(self) -> mock.Mock:
        node_repository_patcher = mock.patch("program_management.ddd.repositories.node.NodeRepository", autospec=True)
        mock_node_repository = node_repository_patcher.start()
        self.addCleanup(node_repository_patcher.stop)
        return mock_node_repository

    def test_should_return_none_when_parent_is_not_minor_major_list_choice(self):
        parent_node_training = NodeGroupYearFactory()
        child_node_minor = NodeGroupYearFactory(node_type=education_group_types.MiniTrainingType.OPEN_MINOR)

        self.mock_get_node_identity.return_value = parent_node_training.entity_id
        self.mock_node_repository.get.side_effect = [parent_node_training, child_node_minor]

        get_default_link_type_command = command.GetDefaultLinkType(
            path_to_paste=str(parent_node_training.node_id),
            child_code=child_node_minor.code,
            child_year=child_node_minor.year
        )

        result = get_default_link_type_service.get_default_link_type(get_default_link_type_command)
        self.assertIsNone(result)

    def test_should_return_reference_link_when_parent_is_minor_major_list_choice_and_child_is_minor_or_deepening(self):
        parent_minor_major_list_choice = NodeGroupYearFactory(
            node_type=education_group_types.GroupType.MINOR_LIST_CHOICE
        )
        child_node_minor = NodeGroupYearFactory(node_type=education_group_types.MiniTrainingType.OPEN_MINOR)

        self.mock_get_node_identity.return_value = parent_minor_major_list_choice.entity_id
        self.mock_node_repository.get.side_effect = [parent_minor_major_list_choice, child_node_minor]

        get_default_link_type_command = command.GetDefaultLinkType(
            path_to_paste=str(parent_minor_major_list_choice.node_id),
            child_code=child_node_minor.code,
            child_year=child_node_minor.year
        )

        result = get_default_link_type_service.get_default_link_type(get_default_link_type_command)
        self.assertEqual(
            link_type.LinkTypes.REFERENCE,
            result
        )

    def test_should_return_none_when_parent_not_find(self):
        self.mock_get_node_identity.return_value = None

        get_default_link_type_command = command.GetDefaultLinkType(
            path_to_paste="1",
            child_code='Code',
            child_year=2019
        )

        result = get_default_link_type_service.get_default_link_type(get_default_link_type_command)
        self.assertIsNone(result)

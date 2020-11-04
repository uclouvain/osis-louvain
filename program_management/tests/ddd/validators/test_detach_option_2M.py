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
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase
from django.utils.translation import ngettext
from mock import patch

from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from program_management.ddd.domain import program_tree
from program_management.ddd.domain.exception import CannotDetachOptionsException
from program_management.ddd.validators._detach_option_2M import DetachOptionValidator
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestDetachOptionValidator(TestValidatorValidateMixin, SimpleTestCase):
    def setUp(self) -> None:
        self.mock_repository = mock.Mock()

    def test_should_not_raise_exception_when_node_to_detach_is_not_an_option_and_does_not_contain_options(self):
        working_tree = ProgramTreeFactory(root_node__node_type=TrainingType.PGRM_MASTER_120)
        link = LinkFactory(parent=working_tree.root_node, child__node_type=TrainingType.MASTER_MA_120)
        path_to_detach = program_tree.build_path(working_tree.root_node, link.child)
        self.mock_repository.configure_mock(
            **{"search_from_children.return_value": [working_tree]}
        )

        validator = DetachOptionValidator(working_tree, path_to_detach, self.mock_repository)
        self.assertValidatorNotRaises(validator)

    @patch(
        'program_management.ddd.domain.service.identity_search.ProgramTreeVersionIdentitySearch.get_from_node_identity'
    )
    def test_should_raise_exception_when_node_to_detach_is_an_option_also_present_inside_finality(self, mock_version):
        working_tree = ProgramTreeFactory(root_node__node_type=TrainingType.PGRM_MASTER_120)
        link_root_finality = LinkFactory(parent=working_tree.root_node, child__node_type=TrainingType.MASTER_MA_120)
        link_finality_option = LinkFactory(parent=link_root_finality.child, child__node_type=MiniTrainingType.OPTION)
        link_root_option = LinkFactory(parent=working_tree.root_node, child=link_finality_option.child)

        mock_version.side_effect = [
            SimpleNamespace(version_name='', offer_acronym=link_finality_option.parent.title),
            SimpleNamespace(version_name='', offer_acronym=link_finality_option.child.title),
        ]

        path_to_detach = program_tree.build_path(working_tree.root_node, link_root_option.child)

        self.mock_repository.configure_mock(
            **{"search_from_children.return_value": [working_tree]}
        )

        with self.assertRaises(CannotDetachOptionsException):
            DetachOptionValidator(working_tree, path_to_detach, self.mock_repository).validate()

    def test_should_not_raise_exception_when_node_to_detach_is_a_finality_in_same_tree(self):
        working_tree = ProgramTreeFactory(root_node__node_type=TrainingType.PGRM_MASTER_120)
        link_root_finality = LinkFactory(parent=working_tree.root_node, child__node_type=TrainingType.MASTER_MA_120)

        path_to_detach = program_tree.build_path(working_tree.root_node, link_root_finality.child)

        self.mock_repository.configure_mock(
            **{"search_from_children.return_value": [working_tree]}
        )

        validator = DetachOptionValidator(working_tree, path_to_detach, self.mock_repository)
        self.assertValidatorNotRaises(validator)

    @patch(
        'program_management.ddd.domain.service.identity_search.ProgramTreeVersionIdentitySearch.get_from_node_identity'
    )
    def test_should_raise_exception_when_node_to_detach_is_an_option_also_present_inside_finality_in_another_tree(
            self,
            mock_version
    ):
        working_tree = ProgramTreeFactory(root_node__node_type=TrainingType.PGRM_MASTER_120)
        link_root_option = LinkFactory(parent=working_tree.root_node, child__node_type=MiniTrainingType.OPTION)

        other_tree = ProgramTreeFactory(root_node__node_type=TrainingType.PGRM_MASTER_120)
        link_tree_finality = LinkFactory(parent=other_tree.root_node, child__node_type=TrainingType.MASTER_MA_120)
        link_finality_option = LinkFactory(parent=link_tree_finality.child, child=link_root_option.child)

        mock_version.side_effect = [
            SimpleNamespace(version_name='', offer_acronym=link_finality_option.parent.title),
            SimpleNamespace(version_name='', offer_acronym=link_finality_option.child.title),
        ]

        path_to_detach = program_tree.build_path(working_tree.root_node, link_root_option.child)

        self.mock_repository.configure_mock(
            **{"search_from_children.return_value": [working_tree, other_tree]}
        )

        with self.assertRaises(CannotDetachOptionsException):
            DetachOptionValidator(working_tree, path_to_detach, self.mock_repository).validate()

    @patch(
        'program_management.ddd.domain.service.identity_search.ProgramTreeVersionIdentitySearch.get_from_node_identity'
    )
    def test_should_not_raise_exception_when_node_present_inside_finality_in_other_tree_through_different_parent(
            self,
            mock_version
    ):
        working_tree = ProgramTreeFactory(root_node__node_type=TrainingType.PGRM_MASTER_120)
        link_root_opt_list = LinkFactory(parent=working_tree.root_node, child__node_type=GroupType.OPTION_LIST_CHOICE)
        link_opt_list_option = LinkFactory(parent=link_root_opt_list.child, child__node_type=MiniTrainingType.OPTION)

        other_tree = ProgramTreeFactory(root_node__node_type=TrainingType.PGRM_MASTER_120)
        link_tree_finality = LinkFactory(parent=other_tree.root_node, child__node_type=TrainingType.MASTER_MA_120)
        link_finality_list = LinkFactory(parent=link_tree_finality.child, child__node_type=GroupType.OPTION_LIST_CHOICE)
        LinkFactory(parent=link_finality_list.child, child=link_opt_list_option.child)

        mock_version.side_effect = [
            SimpleNamespace(version_name='', offer_acronym=link_opt_list_option.parent.title),
            SimpleNamespace(version_name='', offer_acronym=link_opt_list_option.child.title),
        ]

        path_to_detach = program_tree.build_path(
            working_tree.root_node,
            link_root_opt_list.child,
            link_opt_list_option.child
        )
        self.mock_repository.configure_mock(
            **{"search_from_children.return_value": [working_tree]}
        )

        validator = DetachOptionValidator(working_tree, path_to_detach, self.mock_repository)
        self.assertValidatorNotRaises(validator)

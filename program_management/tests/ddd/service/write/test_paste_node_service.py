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
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.utils.translation import gettext as _

import osis_common.ddd.interface
import program_management.ddd.command
import program_management.ddd.service.write.paste_element_service
from base.ddd.utils import business_validator
from base.ddd.utils.validation_message import MessageLevel
from base.models.enums.education_group_types import TrainingType
from program_management.ddd.repositories import node as node_repositoriy
from program_management.ddd.domain import program_tree, link
from program_management.ddd.service.read import check_paste_node_service
from program_management.ddd.service.write import paste_element_service
from program_management.ddd.validators.validators_by_business_action import PasteNodeValidatorList, \
    CheckPasteNodeValidatorList
from program_management.tests.ddd.factories.commands.paste_element_command import PasteElementCommandFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.service.mixins import ValidatorPatcherMixin


class TestPasteNode(TestCase, ValidatorPatcherMixin):

    def setUp(self):
        self.root_node = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        self.tree = ProgramTreeFactory(root_node=self.root_node)
        self.node_to_paste = NodeGroupYearFactory()

        self._patch_persist_tree()
        self._patch_load_tree()
        self._patch_load_child_node_to_attach()
        self.paste_command = PasteElementCommandFactory(
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_where_to_paste=str(self.tree.root_node.node_id)
        )

    def _patch_persist_tree(self):
        patcher_persist = patch("program_management.ddd.repositories.persist_tree.persist")
        self.addCleanup(patcher_persist.stop)
        self.mock_persist = patcher_persist.start()

    def _patch_load_tree(self):
        patcher_load = patch("program_management.ddd.repositories.load_tree.load")
        self.addCleanup(patcher_load.stop)
        self.mock_load_tree = patcher_load.start()
        self.mock_load_tree.return_value = self.tree

    def _patch_load_child_node_to_attach(self):
        patcher_load = patch.object(node_repositoriy.NodeRepository, "get")
        self.addCleanup(patcher_load.stop)
        self.mock_load = patcher_load.start()
        self.mock_load.return_value = self.node_to_paste

    @patch.object(program_tree.ProgramTree, 'paste_node')
    def test_should_return_link_identity_and_persist_when_paste_valid(self, mock_attach_node):
        mock_attach_node.return_value = LinkFactory(parent=self.root_node, child=self.node_to_paste)
        result = program_management.ddd.service.write.paste_element_service.paste_element(self.paste_command)
        expected_result = link.LinkIdentity(
            parent_code=self.root_node.code,
            child_code=self.node_to_paste.code,
            parent_year=self.root_node.year,
            child_year=self.node_to_paste.year
        )

        self.assertEqual(result, expected_result)
        self.assertTrue(self.mock_persist.called)

    @patch.object(program_tree.ProgramTree, 'paste_node')
    def test_should_propagate_exception_when_paste_raises_one(self, mock_attach_node):
        mock_attach_node.side_effect = osis_common.ddd.interface.BusinessExceptions(["error_message_text"])

        with self.assertRaises(osis_common.ddd.interface.BusinessExceptions):
            program_management.ddd.service.write.paste_element_service.paste_element(self.paste_command)

    @patch.object(program_tree.ProgramTree, 'detach_node')
    @mock.patch('program_management.ddd.service.read.search_program_trees_using_node_service'
                '.search_program_trees_using_node')
    def test_when_path_to_detach_is_set_then_should_call_detach(self, mock_search_trees, mock_detach):
        other_tree = ProgramTreeFactory()
        LinkFactory(parent=other_tree.root_node, child=self.node_to_paste)
        self.mock_load_tree.side_effect = [self.tree, other_tree]
        mock_search_trees.return_value = []
        self.mock_validator(PasteNodeValidatorList, ['Success message'], level=MessageLevel.SUCCESS)
        paste_command_with_path_to_detach_set = PasteElementCommandFactory(
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_where_to_paste=str(self.tree.root_node.node_id),
            path_where_to_detach=program_tree.build_path(other_tree.root_node, self.node_to_paste)
        )
        paste_element_service.paste_element(paste_command_with_path_to_detach_set)
        self.assertTrue(mock_detach.called)


class TestCheckPaste(SimpleTestCase, ValidatorPatcherMixin):
    def setUp(self) -> None:
        self.tree = ProgramTreeFactory()
        self.node_to_attach_from = NodeGroupYearFactory()
        LinkFactory(parent=self.tree.root_node, child=self.node_to_attach_from)
        self.path = "|".join([str(self.tree.root_node.node_id), str(self.node_to_attach_from.node_id)])

        self.node_to_paste = NodeGroupYearFactory()

        self._patch_load_tree()
        self._patch_load_node()
        self.mock_check_paste_validator = self._path_validator()

    def _patch_load_node(self):
        patcher_load_nodes = mock.patch.object(
            node_repositoriy.NodeRepository,
            "get"
        )
        self.mock_load_node = patcher_load_nodes.start()
        self.mock_load_node.return_value = self.node_to_paste
        self.addCleanup(patcher_load_nodes.stop)

    def _patch_load_tree(self):
        patcher_load_tree = mock.patch(
            "program_management.ddd.repositories.load_tree.load"
        )
        self.mock_load_tree = patcher_load_tree.start()
        self.mock_load_tree.return_value = self.tree
        self.addCleanup(patcher_load_tree.stop)

    def _path_validator(self):
        patch_validator = mock.patch.object(
            CheckPasteNodeValidatorList, "validate"
        )
        mock_validator = patch_validator.start()
        mock_validator.return_value = True
        self.addCleanup(patch_validator.stop)
        return mock_validator

    def test_should_propagate_error_when_validator_raises_exception(self):
        self.mock_check_paste_validator.side_effect = osis_common.ddd.interface.BusinessExceptions(["an error"])
        check_command = program_management.ddd.command.CheckPasteNodeCommand(
            root_id=self.tree.root_node.node_id,
            node_to_past_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_to_paste=self.path,
            path_to_detach=None
        )
        with self.assertRaises(osis_common.ddd.interface.BusinessExceptions):
            check_paste_node_service.check_paste(check_command)

    def test_should_return_none_when_validator_do_not_raise_exception(self):
        check_command = program_management.ddd.command.CheckPasteNodeCommand(
            root_id=self.tree.root_node.node_id,
            node_to_past_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_to_paste=self.path,
            path_to_detach=None
        )
        self.assertIsNone(check_paste_node_service.check_paste(check_command))

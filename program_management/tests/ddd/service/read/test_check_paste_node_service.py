#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import SimpleTestCase

import program_management.ddd
from osis_common.ddd.interface import BusinessExceptions
from program_management.ddd.repositories import node as node_repositoriy
from program_management.ddd.service.read import check_paste_node_service
from program_management.ddd.validators.validators_by_business_action import CheckPasteNodeValidatorList
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.service.mixins import ValidatorPatcherMixin


# TODO refactor
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
        self.mock_check_paste_validator.side_effect = BusinessExceptions(["an error"])
        check_command = program_management.ddd.command.CheckPasteNodeCommand(
            root_id=self.tree.root_node.node_id,
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_to_paste=self.path,
            path_to_detach=None
        )
        with self.assertRaises(BusinessExceptions):
            check_paste_node_service.check_paste(check_command)

    def test_should_return_none_when_validator_do_not_raise_exception(self):
        check_command = program_management.ddd.command.CheckPasteNodeCommand(
            root_id=self.tree.root_node.node_id,
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_to_paste=self.path,
            path_to_detach=None
        )
        self.assertIsNone(check_paste_node_service.check_paste(check_command))
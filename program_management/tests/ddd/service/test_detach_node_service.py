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
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from base.ddd.utils.validation_message import MessageLevel, BusinessValidationMessage, BusinessValidationMessageList
from base.models.enums.education_group_types import TrainingType
from program_management.ddd.domain import program_tree
from program_management.ddd.domain.program_tree import build_path, ProgramTree
from program_management.ddd.service import detach_node_service
from program_management.ddd.validators._has_or_is_prerequisite import IsPrerequisiteValidator
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipListFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeEducationGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.service.mixins import ValidatorPatcherMixin


class TestDetachNode(SimpleTestCase, ValidatorPatcherMixin):

    def setUp(self):
        self.root_node = NodeEducationGroupYearFactory(
            node_type=TrainingType.BACHELOR,
            node_id=1
        )
        self.link = LinkFactory(parent=self.root_node, child=NodeLearningUnitYearFactory(node_id=2))
        self.tree = ProgramTreeFactory(
            root_node=self.root_node,
            authorized_relationships=AuthorizedRelationshipListFactory()
        )
        self.root_path = str(self.root_node.node_id)
        self.node_to_detach = self.link.child
        self.path_to_detach = build_path(self.link.parent, self.link.child)

        self._patch_persist_tree()
        self._patch_load_tree()
        self._patch_load_trees_from_children()

    def _patch_persist_tree(self):
        patcher_persist = patch("program_management.ddd.repositories.persist_tree.persist")
        self.addCleanup(patcher_persist.stop)
        self.mock_persist = patcher_persist.start()

    def _patch_load_tree(self):
        patcher_load = patch("program_management.ddd.repositories.load_tree.load")
        self.addCleanup(patcher_load.stop)
        self.mock_load = patcher_load.start()
        self.mock_load.return_value = self.tree

    def _patch_load_trees_from_children(self):
        patcher_load = patch("program_management.ddd.repositories.load_tree.load_trees_from_children")
        self.addCleanup(patcher_load.stop)
        self.mock_load_tress_from_children = patcher_load.start()
        self.mock_load_tress_from_children.return_value = [self.tree]

    def test_when_path_to_detach_is_none(self):
        path_to_detach = None
        result = detach_node_service.detach_node(path_to_detach)
        expected_result = [BusinessValidationMessage(_('Invalid tree path'))]
        self.assertListEqual(result.messages, expected_result)

    @patch.object(program_tree.ProgramTree, 'detach_node')
    def test_when_tree_detach_node_is_valid(self, mock_detach_node):
        validator_message = BusinessValidationMessage('Success message', level=MessageLevel.SUCCESS)
        mock_detach_node.return_value = True, [validator_message]
        result = detach_node_service.detach_node(self.path_to_detach)
        expected_result = [validator_message]
        self.assertListEqual(result.messages, expected_result)

    @patch.object(program_tree.ProgramTree, 'detach_node')
    def test_when_tree_detach_node_is_not_valid(self, mock_detach_node):
        validator_message = BusinessValidationMessage('error message text', level=MessageLevel.ERROR)
        mock_detach_node.return_value = False, [validator_message]
        result = detach_node_service.detach_node(self.path_to_detach)
        expected_result = [validator_message]
        self.assertListEqual(result.messages, expected_result)

    @patch.object(ProgramTree, 'detach_node', return_value=(True, []))
    def test_when_commit_is_true(self, mock):
        detach_node_service.detach_node(self.path_to_detach, commit=True)
        self.assertTrue(self.mock_persist.called)

    def test_when_commit_is_false(self):
        detach_node_service.detach_node(self.path_to_detach, commit=False)
        assertion_message = "Should not persist any data into database. " \
                            "It only tests and applies detach action on the in-memory object."
        self.assertFalse(self.mock_persist.called, assertion_message)

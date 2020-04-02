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

from base.ddd.utils.validation_message import MessageLevel, BusinessValidationMessage
from base.models.enums.education_group_types import TrainingType
from base.models.enums.link_type import LinkTypes
from program_management.ddd.domain import program_tree
from program_management.ddd.service import attach_node_service
from program_management.ddd.validators._attach_finality_end_date import AttachFinalityEndDateValidator
from program_management.ddd.validators._attach_option import AttachOptionsValidator
from program_management.ddd.validators._authorized_relationship import AttachAuthorizedRelationshipValidator
from program_management.ddd.validators.validators_by_business_action import AttachNodeValidatorList
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeEducationGroupYearFactory, NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.service.mixins import ValidatorPatcherMixin


class TestAttachNode(SimpleTestCase, ValidatorPatcherMixin):

    def setUp(self):
        self.root_node = NodeEducationGroupYearFactory()
        self.tree = ProgramTreeFactory(root_node=self.root_node)
        self.root_path = str(self.root_node.node_id)
        self.node_to_attach = NodeEducationGroupYearFactory()
        self.node_to_attach_type = NodeType.EDUCATION_GROUP

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

    @patch.object(program_tree.ProgramTree, 'attach_node')
    def test_when_attach_node_action_is_valid(self, mock_attach_node):
        validator_message = BusinessValidationMessage('Success message', level=MessageLevel.SUCCESS)
        mock_attach_node.return_value = [validator_message]
        result = attach_node_service.attach_node(
            self.tree.root_node.node_id,
            self.node_to_attach.node_id,
            self.node_to_attach_type,
            self.root_path
        )
        self.assertEqual(result[0], validator_message)
        self.assertEqual(len(result), 1)

    @patch.object(program_tree.ProgramTree, 'attach_node')
    def test_when_attach_node_action_is_not_valid(self, mock_attach_node):
        validator_message = BusinessValidationMessage('error message text', level=MessageLevel.ERROR)
        mock_attach_node.return_value = [validator_message]
        result = attach_node_service.attach_node(
            self.tree.root_node.node_id,
            self.node_to_attach.node_id,
            self.node_to_attach_type,
            self.root_path
        )
        self.assertEqual(result[0], validator_message)
        self.assertEqual(len(result), 1)

    @patch('program_management.ddd.repositories.load_tree.load_trees_from_children')
    def test_when_node_used_as_reference_is_not_valid(self, mock_load):
        link1 = LinkFactory(child=self.root_node, link_type=LinkTypes.REFERENCE)
        link2 = LinkFactory(child=self.root_node, link_type=LinkTypes.REFERENCE)

        mock_load.return_value = [
            ProgramTreeFactory(root_node=link1.parent),
            ProgramTreeFactory(root_node=link2.parent)
        ]
        self.mock_validator(AttachNodeValidatorList, [])
        self.mock_validator(AttachAuthorizedRelationshipValidator, ['error link reference'])

        result = attach_node_service.attach_node(
            self.tree.root_node,
            self.node_to_attach.node_id,
            self.node_to_attach_type,
            self.root_path
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].message, 'error link reference')
        self.assertEqual(result[0].level, MessageLevel.ERROR)

    @patch('program_management.ddd.repositories.load_tree.load_trees_from_children')
    def test_when_node_used_as_reference_is_valid(self, mock_load):
        link1 = LinkFactory(child=self.root_node, link_type=LinkTypes.REFERENCE)
        link2 = LinkFactory(child=self.root_node, link_type=LinkTypes.REFERENCE)

        mock_load.return_value = [
            ProgramTreeFactory(root_node=link1.parent),
            ProgramTreeFactory(root_node=link2.parent)
        ]
        self.mock_validator(AttachNodeValidatorList, [_('Success message')], level=MessageLevel.SUCCESS)
        self.mock_validator(AttachAuthorizedRelationshipValidator, [])

        result = attach_node_service.attach_node(
            self.tree.root_node,
            self.node_to_attach.node_id,
            self.node_to_attach_type,
            self.root_path
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].message, _('Success message'))
        self.assertEqual(result[0].level, MessageLevel.SUCCESS)

    def test_when_commit_is_true(self):
        self.mock_validator(AttachNodeValidatorList, [_('Success message')], level=MessageLevel.SUCCESS)
        attach_node_service.attach_node(
            self.tree.root_node,
            self.node_to_attach.node_id,
            self.node_to_attach_type,
            self.root_path,
            commit=True
        )
        self.assertTrue(self.mock_load_tress_from_children.called)
        self.assertTrue(self.mock_persist.called)

    def test_when_commit_is_false(self):
        self.mock_validator(AttachNodeValidatorList, [_('Success message')], level=MessageLevel.SUCCESS)
        attach_node_service.attach_node(
            self.tree.root_node,
            self.node_to_attach.node_id,
            self.node_to_attach_type,
            self.root_path,
            commit=False
        )
        self.assertFalse(self.mock_persist.called)


class TestValidateEndDateAndOptionFinality(SimpleTestCase, ValidatorPatcherMixin):

    def setUp(self):
        self.root_node = NodeGroupYearFactory(node_type=TrainingType.PGRM_MASTER_120)
        self.tree_2m = ProgramTreeFactory(root_node=self.root_node)
        self.root_path = str(self.root_node.node_id)
        self.node_to_attach_not_finality = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)

        self._patch_load_tree()

    def _patch_load_tree(self):
        patcher_load = patch("program_management.ddd.repositories.load_tree.load")
        self.addCleanup(patcher_load.stop)
        self.mock_load_tree_to_attach = patcher_load.start()
        self.mock_load_tree_to_attach.return_value = ProgramTreeFactory(root_node=self.node_to_attach_not_finality)

    @patch('program_management.ddd.repositories.load_tree.load_trees_from_children')
    def test_when_node_to_attach_is_not_finality(self, mock_load_2m_trees):
        """Unit test only for performance"""
        self.mock_validator(AttachFinalityEndDateValidator, [_('Success message')], level=MessageLevel.SUCCESS)

        attach_node_service._validate_end_date_and_option_finality(self.node_to_attach_not_finality)
        self.assertFalse(mock_load_2m_trees.called)

    @patch('program_management.ddd.repositories.load_tree.load_trees_from_children')
    def test_when_end_date_of_finality_node_to_attach_is_not_valid(self, mock_load_2m_trees):
        mock_load_2m_trees.return_value = [self.tree_2m]
        node_to_attach = NodeGroupYearFactory(node_type=TrainingType.MASTER_MA_120)
        self.mock_load_tree_to_attach.return_value = ProgramTreeFactory(root_node=node_to_attach)
        self.mock_validator(AttachFinalityEndDateValidator, [_('Error end date finality message')])

        result = attach_node_service._validate_end_date_and_option_finality(node_to_attach)
        validator_msg = "Error end date finality message"
        self.assertEqual(result[0].message, validator_msg)

    @patch('program_management.ddd.repositories.load_tree.load_trees_from_children')
    def test_when_end_date_of_finality_children_of_node_to_attach_is_not_valid(self, mock_load_2m_trees):
        mock_load_2m_trees.return_value = [self.tree_2m]
        not_finality = NodeGroupYearFactory(node_type=TrainingType.AGGREGATION)
        finality = NodeGroupYearFactory(node_type=TrainingType.MASTER_MA_120)
        not_finality.add_child(finality)
        self.mock_load_tree_to_attach.return_value = ProgramTreeFactory(root_node=not_finality)
        self.mock_validator(AttachFinalityEndDateValidator, [_('Error end date finality message')])

        result = attach_node_service._validate_end_date_and_option_finality(not_finality)
        validator_msg = "Error end date finality message"
        self.assertEqual(result[0].message, validator_msg)

    @patch('program_management.ddd.repositories.load_tree.load_trees_from_children')
    def test_when_end_date_of_finality_node_to_attach_is_valid(self, mock_load_2m_trees):
        mock_load_2m_trees.return_value = [self.tree_2m]
        finality = NodeGroupYearFactory(node_type=TrainingType.MASTER_MA_120)
        self.mock_load_tree_to_attach.return_value = ProgramTreeFactory(root_node=finality)
        self.mock_validator(AttachFinalityEndDateValidator, [_('Success')], level=MessageLevel.SUCCESS)

        result = attach_node_service._validate_end_date_and_option_finality(finality)
        self.assertEqual([], result)

    @patch('program_management.ddd.repositories.load_tree.load_trees_from_children')
    def test_when_option_validator_not_valid(self, mock_load_2m_trees):
        mock_load_2m_trees.return_value = [self.tree_2m]
        node_to_attach = NodeGroupYearFactory(node_type=TrainingType.MASTER_MA_120)
        self.mock_load_tree_to_attach.return_value = ProgramTreeFactory(root_node=node_to_attach)
        self.mock_validator(AttachOptionsValidator, [_('Error attach option message')])

        result = attach_node_service._validate_end_date_and_option_finality(node_to_attach)
        validator_msg = "Error attach option message"
        self.assertIn(validator_msg, result)

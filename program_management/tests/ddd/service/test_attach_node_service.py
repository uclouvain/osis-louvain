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
from typing import Type
from unittest import mock
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

import program_management.ddd.service.command
from base.ddd.utils import business_validator
from base.ddd.utils.validation_message import MessageLevel, BusinessValidationMessage
from base.models.enums.education_group_types import TrainingType
from base.models.enums.link_type import LinkTypes
from program_management.ddd.domain import program_tree
from program_management.ddd.service import attach_node_service, command
from program_management.ddd.validators._attach_finality_end_date import AttachFinalityEndDateValidator
from program_management.ddd.validators._attach_option import AttachOptionsValidator
from program_management.ddd.validators._authorized_relationship import AttachAuthorizedRelationshipValidator
from program_management.ddd.validators._infinite_recursivity import InfiniteRecursivityTreeValidator
from program_management.ddd.validators._minimum_editable_year import MinimumEditableYearValidator
from program_management.ddd.validators.link import CreateLinkValidatorList
from program_management.ddd.validators.validators_by_business_action import AttachNodeValidatorList
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeEducationGroupYearFactory, NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.service.mixins import ValidatorPatcherMixin


class TestAttachNode(SimpleTestCase, ValidatorPatcherMixin):

    def setUp(self):
        self.root_node = NodeEducationGroupYearFactory(
            node_type=TrainingType.BACHELOR
        )
        self.tree = ProgramTreeFactory(root_node=self.root_node)
        self.root_path = str(self.root_node.node_id)
        self.node_to_attach = NodeEducationGroupYearFactory()
        self.node_to_attach_type = NodeType.EDUCATION_GROUP

        self._patch_persist_tree()
        self._patch_load_tree()
        self._patch_load_trees_from_children()
        self._patch_load_child_node_to_attach()
        self.attach_request = command.AttachNodeCommand(
            root_id=self.tree.root_node.node_id,
            node_id_to_attach=self.node_to_attach.node_id,
            type_of_node_to_attach=self.node_to_attach_type,
            path_where_to_attach=self.root_path,
            commit=False,
            access_condition=None,
            is_mandatory=None,
            block=None,
            link_type=None,
            comment=None,
            comment_english=None,
            relative_credits=None
        )

    def _patch_persist_tree(self):
        patcher_persist = patch("program_management.ddd.repositories.persist_tree.persist")
        self.addCleanup(patcher_persist.stop)
        self.mock_persist = patcher_persist.start()

    def _patch_load_tree(self):
        patcher_load = patch("program_management.ddd.repositories.load_tree.load")
        self.addCleanup(patcher_load.stop)
        self.mock_load = patcher_load.start()
        self.mock_load.return_value = self.tree

    def _patch_load_child_node_to_attach(self):
        patcher_load = patch("program_management.ddd.repositories.load_node.load_by_type")
        self.addCleanup(patcher_load.stop)
        self.mock_load = patcher_load.start()
        self.mock_load.return_value = self.node_to_attach

    def _patch_load_trees_from_children(self):
        patcher_load = patch("program_management.ddd.repositories.load_tree.load_trees_from_children")
        self.addCleanup(patcher_load.stop)
        self.mock_load_tress_from_children = patcher_load.start()

    @patch.object(program_tree.ProgramTree, 'attach_node')
    def test_when_attach_node_action_is_valid(self, mock_attach_node):
        validator_message = BusinessValidationMessage('Success message', level=MessageLevel.SUCCESS)
        mock_attach_node.return_value = [validator_message]
        result = attach_node_service.attach_node(self.attach_request)
        self.assertEqual(result[0], validator_message)
        self.assertEqual(len(result), 1)

    @patch.object(program_tree.ProgramTree, 'attach_node')
    def test_when_attach_node_action_is_not_valid(self, mock_attach_node):
        validator_message = BusinessValidationMessage('error message text', level=MessageLevel.ERROR)
        mock_attach_node.return_value = [validator_message]
        result = attach_node_service.attach_node(self.attach_request)
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

        result = attach_node_service.attach_node(self.attach_request)
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

        result = attach_node_service.attach_node(self.attach_request)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].message, _('Success message'))
        self.assertEqual(result[0].level, MessageLevel.SUCCESS)

    def test_when_commit_is_true_then_persist_modification(self):
        self.mock_validator(AttachNodeValidatorList, [_('Success message')], level=MessageLevel.SUCCESS)
        attach_request_with_commit_set_to_true = self.attach_request._replace(commit=True)
        attach_node_service.attach_node(attach_request_with_commit_set_to_true)
        self.assertTrue(self.mock_load_tress_from_children.called)
        self.assertTrue(self.mock_persist.called)

    def test_when_commit_is_false_then_sould_not_persist_modification(self):
        self.mock_validator(AttachNodeValidatorList, [_('Success message')], level=MessageLevel.SUCCESS)
        attach_node_service.attach_node(self.attach_request)
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


class TestCheckAttach(SimpleTestCase):
    def setUp(self) -> None:
        self.tree = ProgramTreeFactory()
        self.node_to_attach_from = NodeEducationGroupYearFactory()
        LinkFactory(parent=self.tree.root_node, child=self.node_to_attach_from)
        self.path = "|".join([str(self.tree.root_node.node_id), str(self.node_to_attach_from.node_id)])

        self.node_to_attach_1 = NodeEducationGroupYearFactory()
        self.node_to_attach_2 = NodeEducationGroupYearFactory()

        self._patch_validate_end_date_and_option_finality()
        self._patch_load_tree()
        self._patch_load_node()
        self.mock_create_link_validator = self._patch_validator_is_valid(CreateLinkValidatorList)
        self.mock_minimum_year_editable = self._patch_validator_is_valid(MinimumEditableYearValidator)
        self.mock_infinite_recursivity_tree = self._patch_validator_is_valid(InfiniteRecursivityTreeValidator)

    def _patch_load_node(self):
        patcher_load_nodes = mock.patch(
            "program_management.ddd.repositories.load_node.load_by_type"
        )
        self.mock_load_node = patcher_load_nodes.start()
        self.mock_load_node.side_effect = [self.node_to_attach_1, self.node_to_attach_2]
        self.addCleanup(patcher_load_nodes.stop)

    def _patch_load_tree(self):
        patcher_load_tree = mock.patch(
            "program_management.ddd.repositories.load_tree.load"
        )
        self.mock_load_tree = patcher_load_tree.start()
        self.mock_load_tree.return_value = self.tree
        self.addCleanup(patcher_load_tree.stop)

    def _patch_validate_end_date_and_option_finality(self):
        patcher_validate_end_date_and_option_finality = mock.patch(
            "program_management.ddd.service.attach_node_service._validate_end_date_and_option_finality"
        )
        self.mock_validate_end_date_and_option_finality = patcher_validate_end_date_and_option_finality.start()
        self.mock_validate_end_date_and_option_finality.return_value = []
        self.addCleanup(patcher_validate_end_date_and_option_finality.stop)

    def _patch_validator_is_valid(self, validator_class: Type[business_validator.BusinessValidator]):
        patch_validator = mock.patch.object(
            validator_class, "is_valid"
        )
        mock_validator = patch_validator.start()
        mock_validator.return_value = True
        self.addCleanup(patch_validator.stop)
        return mock_validator

    def test_should_call_return_error_if_no_nodes_to_attach(self):
        check_command = command.CheckAttachNodeCommand(
            root_id=self.tree.root_node.node_id,
            nodes_to_attach=[],
            path_where_to_attach=self.path
        )
        result = attach_node_service.check_attach(check_command)
        self.assertIn(_("Please select an item before adding it"), result)

    def test_should_call_validate_end_date_and_option_finality(self):
        check_command = command.CheckAttachNodeCommand(
            root_id=self.tree.root_node.node_id,
            nodes_to_attach=[
                (self.node_to_attach_1.node_id, self.node_to_attach_1.node_type),
                (self.node_to_attach_2.node_id, self.node_to_attach_2.node_type)
            ],
            path_where_to_attach=self.path
        )
        attach_node_service.check_attach(check_command)

        self.assertEqual(self.mock_validate_end_date_and_option_finality.call_count, 2)

    def test_should_call_specific_validators(self):
        check_command = command.CheckAttachNodeCommand(
            root_id=self.tree.root_node.node_id,
            nodes_to_attach=[
                (self.node_to_attach_1.node_id, self.node_to_attach_1.node_type),
                (self.node_to_attach_2.node_id, self.node_to_attach_2.node_type)
            ],
            path_where_to_attach=self.path
        )
        attach_node_service.check_attach(check_command)

        self.assertEqual(self.mock_create_link_validator.call_count, 2)
        self.assertEqual(self.mock_minimum_year_editable.call_count, 2)
        self.assertEqual(self.mock_infinite_recursivity_tree.call_count, 2)

    def test_should_return_validation_messages_if_any(self):
        check_command = command.CheckAttachNodeCommand(
            root_id=self.tree.root_node.node_id,
            nodes_to_attach=[
                (self.node_to_attach_1.node_id, self.node_to_attach_1.node_type),
                (self.node_to_attach_2.node_id, self.node_to_attach_2.node_type)
            ],
            path_where_to_attach=self.path
        )
        self.mock_validate_end_date_and_option_finality.return_value = ["Validation error"]
        result = attach_node_service.check_attach(check_command)

        self.assertEqual(
            result,
            ["Validation error", "Validation error"]
        )

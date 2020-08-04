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

import osis_common.ddd.interface
from base.ddd.utils import business_validator
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.validators import _validate_end_date_and_option_finality
from program_management.ddd.validators._authorized_link_type import AuthorizedLinkTypeValidator
from program_management.ddd.validators._authorized_relationship import \
    AuthorizedRelationshipLearningUnitValidator, PasteAuthorizedRelationshipValidator, \
    DetachAuthorizedRelationshipValidator
from program_management.ddd.validators._authorized_relationship_for_all_trees import \
    ValidateAuthorizedRelationshipForAllTrees
from program_management.ddd.validators._authorized_root_type_for_prerequisite import AuthorizedRootTypeForPrerequisite
from program_management.ddd.validators._block_validator import BlockValidator
from program_management.ddd.validators._detach_option_2M import DetachOptionValidator
from program_management.ddd.validators._detach_root import DetachRootValidator
from program_management.ddd.validators._empty_program_tree import EmptyProgramTreeValidator
from program_management.ddd.validators._has_or_is_prerequisite import IsPrerequisiteValidator
from program_management.ddd.validators._infinite_recursivity import InfiniteRecursivityTreeValidator
from program_management.ddd.validators._minimum_editable_year import \
    MinimumEditableYearValidator
from program_management.ddd.validators._node_have_link import NodeHaveLinkValidator
from program_management.ddd.validators._prerequisite_expression_syntax import PrerequisiteExpressionSyntaxValidator
from program_management.ddd.validators._prerequisites_items import PrerequisiteItemsValidator
from program_management.ddd.validators._relative_credits import RelativeCreditsValidator
from program_management.ddd.validators.link import CreateLinkValidatorList


class PasteNodeValidatorList(business_validator.BusinessListValidator):
    def __init__(
            self,
            tree: 'ProgramTree',
            node_to_paste: 'Node',
            paste_command: command.PasteElementCommand,
            tree_repository: 'ProgramTreeRepository'
    ):
        path = paste_command.path_where_to_paste
        link_type = paste_command.link_type
        block = paste_command.block

        if node_to_paste.is_group_or_mini_or_training():
            self.validators = [
                CreateLinkValidatorList(tree.get_node(path), node_to_paste),
                PasteAuthorizedRelationshipValidator(tree, node_to_paste, tree.get_node(path)),
                MinimumEditableYearValidator(tree),
                InfiniteRecursivityTreeValidator(tree, node_to_paste, path),
                AuthorizedLinkTypeValidator(tree.root_node, node_to_paste, link_type),
                BlockValidator(block),
                _validate_end_date_and_option_finality.ValidateEndDateAndOptionFinality(node_to_paste, tree_repository),
                ValidateAuthorizedRelationshipForAllTrees(tree, node_to_paste, path, tree_repository)
            ]

        elif node_to_paste.is_learning_unit():
            self.validators = [
                CreateLinkValidatorList(tree.get_node(path), node_to_paste),
                AuthorizedRelationshipLearningUnitValidator(tree, node_to_paste, tree.get_node(path)),
                MinimumEditableYearValidator(tree),
                InfiniteRecursivityTreeValidator(tree, node_to_paste, path),
                AuthorizedLinkTypeValidator(tree.root_node, node_to_paste, link_type),
                BlockValidator(block),
                ValidateAuthorizedRelationshipForAllTrees(tree, node_to_paste, path, tree_repository)
            ]

        else:
            raise AttributeError("Unknown instance of node")
        super().__init__()

    def validate(self):
        error_messages = []
        for validator in self.validators:
            try:
                validator.validate()
            except osis_common.ddd.interface.BusinessExceptions as business_exception:
                error_messages.extend(business_exception.messages)

        if error_messages:
            raise osis_common.ddd.interface.BusinessExceptions(error_messages)


class CheckPasteNodeValidatorList(business_validator.BusinessListValidator):
    def __init__(
            self,
            tree: 'ProgramTree',
            node_to_paste: 'Node',
            check_paste_command: command.CheckPasteNodeCommand,
            tree_repository: 'ProgramTreeRepository'
    ):
        path = check_paste_command.path_to_paste

        if node_to_paste.is_group_or_mini_or_training():
            self.validators = [
                CreateLinkValidatorList(tree.get_node(path), node_to_paste),
                MinimumEditableYearValidator(tree),
                InfiniteRecursivityTreeValidator(tree, node_to_paste, path),
                _validate_end_date_and_option_finality.ValidateEndDateAndOptionFinality(node_to_paste, tree_repository),
            ]

        elif node_to_paste.is_learning_unit():
            self.validators = [
                CreateLinkValidatorList(tree.get_node(path), node_to_paste),
                AuthorizedRelationshipLearningUnitValidator(tree, node_to_paste, tree.get_node(path)),
                MinimumEditableYearValidator(tree),
                InfiniteRecursivityTreeValidator(tree, node_to_paste, path),
            ]

        else:
            raise AttributeError("Unknown instance of node")
        super().__init__()

    def validate(self):
        error_messages = []
        for validator in self.validators:
            try:
                validator.validate()
            except osis_common.ddd.interface.BusinessExceptions as business_exception:
                error_messages.extend(business_exception.messages)

        if error_messages:
            raise osis_common.ddd.interface.BusinessExceptions(error_messages)


class DetachNodeValidatorList(business_validator.BusinessListValidator):

    def __init__(
            self,
            tree: 'ProgramTree',
            node_to_detach: 'Node',
            path_to_parent: 'Path',
            tree_repository: 'ProgramTreeRepository') -> None:
        detach_from = tree.get_node(path_to_parent)

        if node_to_detach.is_group_or_mini_or_training():
            path_to_node_to_detach = path_to_parent + '|' + str(node_to_detach.node_id)
            self.validators = [
                DetachRootValidator(tree, path_to_parent),
                MinimumEditableYearValidator(tree),
                DetachAuthorizedRelationshipValidator(tree, node_to_detach, detach_from),
                IsPrerequisiteValidator(tree, path_to_parent, node_to_detach),
                DetachOptionValidator(tree, path_to_node_to_detach, tree_repository),
            ]

        elif node_to_detach.is_learning_unit():
            self.validators = [
                AuthorizedRelationshipLearningUnitValidator(tree, node_to_detach, detach_from),
                MinimumEditableYearValidator(tree),
                IsPrerequisiteValidator(tree, path_to_parent, node_to_detach),
            ]

        else:
            raise AttributeError("Unknown instance of node")
        super().__init__()

    def validate(self):
        error_messages = []
        for validator in self.validators:
            try:
                validator.validate()
            except osis_common.ddd.interface.BusinessExceptions as business_exception:
                error_messages.extend(business_exception.messages)

        if error_messages:
            raise osis_common.ddd.interface.BusinessExceptions(error_messages)


class UpdatePrerequisiteValidatorList(business_validator.BusinessListValidator):

    def __init__(
            self,
            prerequisite_string: 'PrerequisiteExpression',
            node: 'NodeLearningUnitYear',
            program_tree: 'ProgramTree'
    ):
        self.validators = [
            AuthorizedRootTypeForPrerequisite(program_tree.root_node),
            PrerequisiteExpressionSyntaxValidator(prerequisite_string),
            PrerequisiteItemsValidator(prerequisite_string, node, program_tree)
        ]
        super().__init__()


class UpdateLinkValidatorList(business_validator.BusinessListValidator):
    def __init__(
            self,
            parent_node: 'Node',
            child_node: 'Node',
            link: 'Link',
    ):
        self.validators = [
            AuthorizedLinkTypeValidator(parent_node, child_node, link.link_type),
            BlockValidator(link.block),
            RelativeCreditsValidator(link.relative_credits)
        ]
        super().__init__()


class DeleteProgramTreeValidatorList(business_validator.BusinessListValidator):
    def __init__(
            self,
            program_tree: 'ProgramTree',
    ):
        self.validators = [
            EmptyProgramTreeValidator(program_tree),
            NodeHaveLinkValidator(program_tree.root_node)
        ]
        super().__init__()


class DeleteStandardVersionValidatorList(business_validator.BusinessListValidator):
    def __init__(
            self,
            program_tree_version: 'ProgramTreeVersion',
    ):
        self.validators = []
        super().__init__()

##############################################################################
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from typing import Optional

from base.ddd.utils import business_validator
from base.ddd.utils.business_validator import BusinessListValidator, MultipleExceptionBusinessListValidator
from base.models.enums.link_type import LinkTypes
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.validators._authorized_link_type import AuthorizedLinkTypeValidator
from program_management.ddd.validators._authorized_relationship import \
    AuthorizedRelationshipLearningUnitValidator, DetachAuthorizedRelationshipValidator, \
    UpdateLinkAuthorizedRelationshipValidator
from program_management.ddd.validators._authorized_relationship_for_all_trees import \
    ValidateAuthorizedRelationshipForAllTrees
from program_management.ddd.validators._authorized_root_type_for_prerequisite import AuthorizedRootTypeForPrerequisite
from program_management.ddd.validators._block_validator import BlockValidator
from program_management.ddd.validators._copy_check_end_date_program_tree import CheckProgramTreeEndDateValidator
from program_management.ddd.validators._copy_check_end_date_tree_version import CheckTreeVersionEndDateValidator
from program_management.ddd.validators._delete_check_versions_end_date import CheckVersionsEndDateValidator
from program_management.ddd.validators._detach_option_2M import DetachOptionValidator
from program_management.ddd.validators._detach_root import DetachRootValidator
from program_management.ddd.validators._empty_program_tree import EmptyProgramTreeValidator
from program_management.ddd.validators._end_date_between_finalities_and_masters import \
    CheckEndDateBetweenFinalitiesAndMasters2M
from program_management.ddd.validators._fill_check_tree_from import CheckValidTreeVersionToFillFrom
from program_management.ddd.validators._fill_check_tree_to import CheckValidTreeVersionToFillTo
from program_management.ddd.validators._has_or_is_prerequisite import IsHasPrerequisiteForAllTreesValidator
from program_management.ddd.validators._infinite_recursivity import InfiniteRecursivityTreeValidator
from program_management.ddd.validators._match_version import MatchVersionValidator
from program_management.ddd.validators._minimum_editable_year import \
    MinimumEditableYearValidator
from program_management.ddd.validators._node_have_link import NodeHaveLinkValidator
from program_management.ddd.validators._prerequisite_expression_syntax import PrerequisiteExpressionSyntaxValidator
from program_management.ddd.validators._prerequisites_items import PrerequisiteItemsValidator
from program_management.ddd.validators._relative_credits import RelativeCreditsValidator
from program_management.ddd.validators._transition_name_existed import TransitionNameExistedValidator
from program_management.ddd.validators._transition_name_exists import TransitionNameExistsValidator
from program_management.ddd.validators._transition_name_pattern import TransitionNamePatternValidator
from program_management.ddd.validators._update_check_existence_of_transition import CheckExistenceOfTransition
from program_management.ddd.validators._validate_end_date_and_option_finality import ValidateFinalitiesEndDateAndOptions
from program_management.ddd.validators._version_name_existed import VersionNameExistedValidator
from program_management.ddd.validators._version_name_exists import VersionNameExistsValidator
from program_management.ddd.validators._version_name_pattern import VersionNamePatternValidator
from program_management.ddd.validators.link import CreateLinkValidatorList


class PasteNodeValidatorList(MultipleExceptionBusinessListValidator):
    def __init__(
            self,
            tree: 'ProgramTree',
            node_to_paste: 'Node',
            paste_command: command.PasteElementCommand,
            link_type: Optional[LinkTypes],
            tree_repository: 'ProgramTreeRepository',
            version_repository: 'ProgramTreeVersionRepository'
    ):
        path = paste_command.path_where_to_paste
        parent_node = tree.get_node(path)
        block = paste_command.block
        relative_credits = paste_command.relative_credits

        if node_to_paste.is_group_or_mini_or_training():
            self.validators = [
                CreateLinkValidatorList(parent_node, node_to_paste),
                MinimumEditableYearValidator(tree),
                InfiniteRecursivityTreeValidator(tree, node_to_paste, path, tree_repository),
                AuthorizedLinkTypeValidator(tree, node_to_paste, link_type),
                BlockValidator(block),
                ValidateFinalitiesEndDateAndOptions(parent_node, node_to_paste, tree_repository),
                ValidateAuthorizedRelationshipForAllTrees(tree, node_to_paste, path, tree_repository, link_type),
                MatchVersionValidator(parent_node, node_to_paste, tree_repository, version_repository),
                RelativeCreditsValidator(relative_credits),
            ]

        elif node_to_paste.is_learning_unit():
            self.validators = [
                CreateLinkValidatorList(parent_node, node_to_paste),
                AuthorizedRelationshipLearningUnitValidator(tree, node_to_paste, parent_node),
                MinimumEditableYearValidator(tree),
                InfiniteRecursivityTreeValidator(tree, node_to_paste, path, tree_repository),
                AuthorizedLinkTypeValidator(tree, node_to_paste, link_type),
                BlockValidator(block),
                RelativeCreditsValidator(relative_credits),
            ]

        else:
            raise AttributeError("Unknown instance of node")
        super().__init__()


class UpdateLinkValidatorList(MultipleExceptionBusinessListValidator):
    def __init__(
            self,
            tree: 'ProgramTree',
            child_node: 'Node',
            link: 'Link',
    ):
        self.validators = [
            AuthorizedLinkTypeValidator(tree, child_node, link.link_type),
            UpdateLinkAuthorizedRelationshipValidator(tree, child_node),
            BlockValidator(link.block),
            RelativeCreditsValidator(link.relative_credits)
        ]
        super().__init__()


class CheckPasteNodeValidatorList(MultipleExceptionBusinessListValidator):
    def __init__(
            self,
            tree: 'ProgramTree',
            node_to_paste: 'Node',
            check_paste_command: command.CheckPasteNodeCommand,
            tree_repository: 'ProgramTreeRepository',
            tree_version_repository: 'ProgramTreeVersionRepository'
    ):
        path = check_paste_command.path_to_paste

        if node_to_paste.is_group_or_mini_or_training():
            self.validators = [
                CreateLinkValidatorList(tree.get_node(path), node_to_paste),
                MinimumEditableYearValidator(tree),
                InfiniteRecursivityTreeValidator(tree, node_to_paste, path, tree_repository),
                ValidateFinalitiesEndDateAndOptions(tree.get_node(path), node_to_paste, tree_repository),
                MatchVersionValidator(
                    tree.get_node(path),
                    node_to_paste,
                    tree_repository,
                    tree_version_repository
                ),
            ]

        elif node_to_paste.is_learning_unit():
            self.validators = [
                CreateLinkValidatorList(tree.get_node(path), node_to_paste),
                AuthorizedRelationshipLearningUnitValidator(tree, node_to_paste, tree.get_node(path)),
                MinimumEditableYearValidator(tree),
                InfiniteRecursivityTreeValidator(tree, node_to_paste, path, tree_repository),
            ]

        else:
            raise AttributeError("Unknown instance of node")
        super().__init__()


class DetachNodeValidatorList(MultipleExceptionBusinessListValidator):

    def __init__(
            self,
            tree: 'ProgramTree',
            node_to_detach: 'Node',
            path_to_parent: 'Path',
            tree_repository: 'ProgramTreeRepository',
            prerequisite_repository: 'TreePrerequisitesRepository'
    ) -> None:
        detach_from = tree.get_node(path_to_parent)

        prerequisites_validator = IsHasPrerequisiteForAllTreesValidator(
            detach_from,
            node_to_detach,
            tree_repository,
            prerequisite_repository
        )

        if node_to_detach.is_group_or_mini_or_training():
            path_to_node_to_detach = path_to_parent + '|' + str(node_to_detach.node_id)
            self.validators = [
                DetachRootValidator(tree, path_to_node_to_detach),
                MinimumEditableYearValidator(tree),
                DetachAuthorizedRelationshipValidator(tree, node_to_detach, detach_from),
                prerequisites_validator,
                DetachOptionValidator(tree, path_to_node_to_detach, tree_repository),
            ]

        elif node_to_detach.is_learning_unit():
            self.validators = [
                AuthorizedRelationshipLearningUnitValidator(tree, node_to_detach, detach_from),
                MinimumEditableYearValidator(tree),
                prerequisites_validator,
            ]

        else:
            raise AttributeError("Unknown instance of node")
        super().__init__()


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


class DeleteProgramTreeValidatorList(business_validator.BusinessListValidator):
    def __init__(self, program_tree: 'ProgramTree', tree_repository: 'ProgramTreeRepository'):
        self.validators = [
            EmptyProgramTreeValidator(program_tree),
            NodeHaveLinkValidator(program_tree.root_node, tree_repository)
        ]
        super().__init__()


class DeleteSpecificVersionValidatorList(business_validator.BusinessListValidator):
    def __init__(
            self,
            program_tree_version: 'ProgramTreeVersion',
    ):
        self.validators = [
            CheckVersionsEndDateValidator(program_tree_version),
        ]
        super().__init__()


class CopyProgramTreeVersionValidatorList(business_validator.BusinessListValidator):
    def __init__(self, copy_from: 'ProgramTreeVersion'):
        self.validators = [
            CheckTreeVersionEndDateValidator(copy_from)
        ]
        super().__init__()


class FillProgramTreeVersionValidatorList(MultipleExceptionBusinessListValidator):
    def __init__(self, tree_to_fill_from: 'ProgramTreeVersion', tree_to_fill_to: 'ProgramTreeVersion'):
        self.validators = [
            CheckValidTreeVersionToFillTo(tree_to_fill_to),
            CheckValidTreeVersionToFillFrom(tree_to_fill_from, tree_to_fill_to)
        ]
        super().__init__()


class CopyProgramTreeValidatorList(business_validator.BusinessListValidator):
    def __init__(self, copy_from: 'ProgramTree'):
        self.validators = [
            CheckProgramTreeEndDateValidator(copy_from),
        ]
        super().__init__()


class CopyContentProgramTreeValidatorList(MultipleExceptionBusinessListValidator):
    def __init__(self, copy_from: 'ProgramTree', next_year_tree: Optional['ProgramTree']):
        self.validators = [
            CheckProgramTreeEndDateValidator(copy_from),
        ]
        if next_year_tree:
            self.validators.append(
                EmptyProgramTreeValidator(next_year_tree)
            )
        super().__init__()


class FillProgramTreeValidatorList(MultipleExceptionBusinessListValidator):
    def __init__(self, to_tree: 'ProgramTree'):
        self.validators = [
            EmptyProgramTreeValidator(to_tree),
        ]
        super().__init__()


class UpdateProgramTreeVersionValidatorList(MultipleExceptionBusinessListValidator):
    def __init__(self, tree_version: 'ProgramTreeVersion'):
        tree = tree_version.get_tree()
        initial_end_year = tree.root_node.end_year
        tree.root_node.end_year = tree_version.end_year_of_existence
        self.validators = [
            CheckEndDateBetweenFinalitiesAndMasters2M(tree, tree_version.program_tree_repository),
            CheckExistenceOfTransition(tree_version, initial_end_year)
        ]
        super().__init__()


class CreateProgramTreeVersionValidatorList(BusinessListValidator):

    def __init__(self, year: int, offer_acronym: str, version_name: str, transition_name: str):
        self.validators = [
            VersionNameExistsValidator(year, offer_acronym, version_name, transition_name),
        ]
        super().__init__()


class CreateProgramTreeTransitionVersionValidatorList(BusinessListValidator):
    def __init__(self, year: int, offer_acronym: str, version_name: str, transition_name: str):
        self.validators = [
            VersionNameExistsValidator(year, offer_acronym, version_name, transition_name),
            TransitionNamePatternValidator(transition_name=transition_name)
        ]
        super().__init__()


class CheckVersionNameValidatorList(MultipleExceptionBusinessListValidator):
    def __init__(self, year: int, offer_acronym: str, version_name: str, transition_name: str):
        self.validators = [
            VersionNamePatternValidator(version_name),
            VersionNameExistsValidator(year, offer_acronym, version_name, transition_name),
            VersionNameExistedValidator(year, offer_acronym, version_name, transition_name),
        ]
        super().__init__()


class CheckTransitionNameValidatorList(MultipleExceptionBusinessListValidator):
    def __init__(self, year: int, offer_acronym: str, version_name: str, transition_name: str):
        self.validators = [
            TransitionNamePatternValidator(transition_name=transition_name),
            TransitionNameExistsValidator(year, offer_acronym, version_name, transition_name),
            TransitionNameExistedValidator(year, offer_acronym, version_name, transition_name),
        ]
        super().__init__()

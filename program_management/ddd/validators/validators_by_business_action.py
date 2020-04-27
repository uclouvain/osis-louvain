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
from django.utils.translation import gettext as _

from base.ddd.utils.business_validator import BusinessListValidator
from program_management.ddd.business_types import *
from program_management.ddd.validators._authorized_relationship import \
    AuthorizedRelationshipLearningUnitValidator, AttachAuthorizedRelationshipValidator, \
    DetachAuthorizedRelationshipValidator
from program_management.ddd.validators._detach_option_2M import DetachOptionValidator
from program_management.ddd.validators._has_or_is_prerequisite import IsPrerequisiteValidator, HasPrerequisiteValidator
from program_management.ddd.validators._authorized_root_type_for_prerequisite import AuthorizedRootTypeForPrerequisite
from program_management.ddd.validators._infinite_recursivity import InfiniteRecursivityTreeValidator
from program_management.ddd.validators._minimum_editable_year import \
    MinimumEditableYearValidator
from program_management.ddd.validators._prerequisite_expression_syntax import PrerequisiteExpressionSyntaxValidator
from program_management.ddd.validators._prerequisites_items import PrerequisiteItemsValidator
from program_management.ddd.validators.link import CreateLinkValidatorList


class AttachNodeValidatorList(BusinessListValidator):

    success_messages = [
        _('Success message')
    ]

    def __init__(self, tree: 'ProgramTree', node_to_add: 'Node', path: 'Path'):
        if node_to_add.is_group():
            self.validators = [
                CreateLinkValidatorList(tree.get_node(path), node_to_add),
                AttachAuthorizedRelationshipValidator(tree, node_to_add, tree.get_node(path)),
                MinimumEditableYearValidator(tree),
                InfiniteRecursivityTreeValidator(tree, node_to_add, path),
            ]

        elif node_to_add.is_learning_unit():
            self.validators = [
                CreateLinkValidatorList(tree.get_node(path), node_to_add),
                AuthorizedRelationshipLearningUnitValidator(tree, node_to_add, tree.get_node(path)),
                MinimumEditableYearValidator(tree),
                InfiniteRecursivityTreeValidator(tree, node_to_add, path),
            ]

        else:
            raise AttributeError("Unknown instance of node")
        super().__init__()


class DetachNodeValidatorList(BusinessListValidator):

    def __init__(self, tree: 'ProgramTree', node_to_detach: 'Node', path_to_parent: 'Path'):
        detach_from = tree.get_node(path_to_parent)

        if node_to_detach.is_group():
            path_to_node_to_detach = path_to_parent + '|' + str(node_to_detach.node_id)
            self.validators = [
                MinimumEditableYearValidator(tree),
                DetachAuthorizedRelationshipValidator(tree, node_to_detach, detach_from),
                IsPrerequisiteValidator(tree, node_to_detach),
                HasPrerequisiteValidator(tree, node_to_detach),
                DetachOptionValidator(tree, path_to_node_to_detach, [tree]),
            ]

        elif node_to_detach.is_learning_unit():
            self.validators = [
                AuthorizedRelationshipLearningUnitValidator(tree, node_to_detach, detach_from),
                MinimumEditableYearValidator(tree),
                IsPrerequisiteValidator(tree, node_to_detach),
                HasPrerequisiteValidator(tree, node_to_detach),
            ]

        else:
            raise AttributeError("Unknown instance of node")
        super().__init__()

        self.add_success_message(_("\"%(child)s\" has been detached from \"%(parent)s\"") % {
            'child': node_to_detach,
            'parent': detach_from,
        })  # TODO :: unit test


class UpdatePrerequisiteValidatorList(BusinessListValidator):

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

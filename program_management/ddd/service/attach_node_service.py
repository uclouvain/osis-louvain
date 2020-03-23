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
from typing import List

from base.ddd.utils.validation_message import BusinessValidationMessage
from base.models.enums.link_type import LinkTypes
from program_management.ddd.business_types import *
from program_management.ddd.domain.node import factory
from program_management.ddd.repositories import load_tree, persist_tree
from program_management.ddd.validators._attach_finality_end_date import AttachFinalityEndDateValidator
from program_management.ddd.validators._attach_option import AttachOptionsValidator
from program_management.ddd.validators._authorized_relationship import AttachAuthorizedRelationshipValidator


def attach_node(
        root_id: int,
        node_id_to_attach: int,
        type_node_to_attach,
        path: 'Path' = None,
        commit=True,
        **link_attributes
) -> List[BusinessValidationMessage]:
    tree = load_tree.load(root_id)
    node_to_attach = factory.get_node(type_node_to_attach, node_id=node_id_to_attach)
    error_messages = __validate_trees_using_node_as_reference_link(tree, node_to_attach, path)
    error_messages += _validate_end_date_and_option_finality(node_to_attach)
    if error_messages:
        return error_messages
    success_messages = tree.attach_node(node_to_attach, path, **link_attributes)
    if commit:
        persist_tree.persist(tree)
    return success_messages


def __validate_trees_using_node_as_reference_link(
        tree: 'ProgramTree',
        node_to_attach: 'Node',
        path: 'Path'
) -> List[BusinessValidationMessage]:

    error_messages = []
    child_node = tree.get_node(path)
    trees = load_tree.load_trees_from_children([child_node.node_id], link_type=LinkTypes.REFERENCE)
    for tree in trees:
        for parent_from_reference_link in tree.get_parents_using_node_as_reference(child_node):
            validator = AttachAuthorizedRelationshipValidator(tree, node_to_attach, parent_from_reference_link)
            if not validator.is_valid():
                error_messages += validator.error_messages
    return error_messages


def _validate_end_date_and_option_finality(node_to_attach: 'Node') -> List[BusinessValidationMessage]:
    error_messages = []
    tree_from_node_to_attach = load_tree.load(node_to_attach.node_id)
    finality_ids = [n.node_id for n in tree_from_node_to_attach.get_all_finalities()]
    if node_to_attach.is_finality() or finality_ids:
        trees_2m = [
            tree for tree in load_tree.load_trees_from_children(child_branch_ids=finality_ids)
            if tree.is_master_2m()
        ]
        for tree_2m in trees_2m:
            validator = AttachFinalityEndDateValidator(tree_2m, tree_from_node_to_attach)
            if not validator.is_valid():
                error_messages += validator.error_messages
            validator = AttachOptionsValidator(tree_2m, tree_from_node_to_attach)
            if not validator.is_valid():
                error_messages += validator.error_messages
    return error_messages

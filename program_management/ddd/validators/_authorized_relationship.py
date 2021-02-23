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
import copy
from collections import Counter
from typing import List

from base.ddd.utils import business_validator
from base.models.enums.education_group_types import EducationGroupTypesEnum
from base.models.enums.link_type import LinkTypes
from program_management.ddd.business_types import *
from program_management.ddd.domain.exception import ChildTypeNotAuthorizedException, \
    MaximumChildTypesReachedException, MinimumChildTypesNotRespectedException


class UpdateLinkAuthorizedRelationshipValidator(business_validator.BusinessValidator):
    def __init__(self, tree: 'ProgramTree', child_node: 'Node'):
        self.tree = tree
        self.link_updated = self.tree.root_node.get_direct_child(child_node.entity_id)

        super().__init__()

    def validate(self, *args, **kwargs):
        AuthorizedRelationshipValidator(tree=self.tree, link_upserted=self.link_updated).validate()


class PasteAuthorizedRelationshipValidator(business_validator.BusinessValidator):
    def __init__(self, tree: 'ProgramTree', node_to_paste: 'Node', parent_node: 'Node', link_type: LinkTypes = None):
        self.tree = copy.deepcopy(tree)
        self.parent_node = self.tree.get_node_by_code_and_year(parent_node.code, parent_node.year)
        self.link_created = self.parent_node.add_child(node_to_paste, link_type=link_type)

        super().__init__()

    def validate(self):
        AuthorizedRelationshipValidator(tree=self.tree, link_upserted=self.link_created).validate()


class DetachAuthorizedRelationshipValidator(business_validator.BusinessValidator):
    def __init__(self, tree: 'ProgramTree', node_to_detach: 'Node', detach_from: 'Node'):
        super(DetachAuthorizedRelationshipValidator, self).__init__()
        self.node_to_detach = node_to_detach
        self.detach_from = detach_from
        self.tree = tree

    def validate(self):
        tree_copy = copy.copy(self.tree)
        parent_node = tree_copy.get_node_by_code_and_year(self.detach_from.code, self.detach_from.year)
        child_node_to_detach = tree_copy.get_node_by_code_and_year(self.node_to_detach.code, self.node_to_detach.year)
        parent_node.detach_child(child_node_to_detach)

        MinimumChildrenTypeAuthorizedValidator(tree_copy, parent_node).validate()


class AuthorizedRelationshipValidator(business_validator.BusinessValidator):
    def __init__(self, tree: 'ProgramTree', link_upserted: 'Link'):
        self.tree = tree
        self.link = link_upserted

        super().__init__()

    def validate(self, *args, **kwargs):
        if self.link.is_reference() and \
                self._is_child_a_minor_major_or_deepening_inside_a_list_minor_major_choice_parent():
            return
        if self._is_child_a_minor_major_list_inside_a_list_minor_major_choice_parent():
            return

        ChildTypeValidator(self.tree, self.link.parent).validate()
        MinimumChildrenTypeAuthorizedValidator(self.tree, self.link.parent).validate()
        MaximumChildrenTypeAuthorizedValidator(self.tree, self.link.parent).validate()
        if self.link.parent.is_finality_list_choice():
            MaximumFinalitiesAuthorizedValidator(self.tree, self.link.parent).validate()

    def _is_child_a_minor_major_or_deepening_inside_a_list_minor_major_choice_parent(self) -> bool:
        return self.link.parent.is_minor_major_list_choice() and self.link.child.is_minor_major_deepening()

    def _is_child_a_minor_major_list_inside_a_list_minor_major_choice_parent(self) -> bool:
        return self.link.parent.is_minor_major_list_choice() and self.link.child.is_minor_major_list_choice()


class AuthorizedRelationshipLearningUnitValidator(business_validator.BusinessValidator):
    def __init__(self, tree: 'ProgramTree', node_to_attach: 'Node', position_to_attach_from: 'Node'):
        super().__init__()
        self.tree = tree
        self.node_to_attach = node_to_attach
        self.position_to_attach_from = position_to_attach_from

    def validate(self):
        if not self.tree.authorized_relationships.is_authorized(
                self.position_to_attach_from.node_type,
                self.node_to_attach.node_type
        ):
            raise ChildTypeNotAuthorizedException(
                parent_node=self.position_to_attach_from,
                children_nodes=[self.node_to_attach]
            )


class MaximumChildrenTypeAuthorizedValidator(business_validator.BusinessValidator):
    def __init__(self, tree: 'ProgramTree', parent_node: 'Node'):
        super().__init__()
        self.tree = tree
        self.parent_node = parent_node

    def validate(self, *args, **kwargs):
        children_type_that_surpassed_maximum_authorized = self.get_children_types_that_surpass_maximum_allowed()
        if children_type_that_surpassed_maximum_authorized:
            raise MaximumChildTypesReachedException(self.parent_node, children_type_that_surpassed_maximum_authorized)

    def get_children_types_that_surpass_maximum_allowed(self) -> List['EducationGroupTypesEnum']:
        children_types_counter = Counter(self.parent_node.get_children_types(include_nodes_used_as_reference=True))
        return [
            children_type for children_type, number_children in children_types_counter.items()
            if self._is_maximum_children_surpassed(children_type, number_children)
        ]

    def _is_maximum_children_surpassed(self, children_type, number_children) -> bool:
        authorized_relationship = self.tree.authorized_relationships.get_authorized_relationship(
            self.parent_node.node_type,
            children_type
        )
        maximum_children_authorized = authorized_relationship.max_count_authorized if authorized_relationship else 0
        return number_children > maximum_children_authorized


class MinimumChildrenTypeAuthorizedValidator(business_validator.BusinessValidator):
    def __init__(self, tree: 'ProgramTree', parent_node: 'Node'):
        super().__init__()
        self.tree = tree
        self.parent_node = parent_node

    def validate(self, *args, **kwargs):
        children_type_that_are_inferior_to_minimum = self.get_children_types_that_subceed_minimum_required()
        if children_type_that_are_inferior_to_minimum:
            raise MinimumChildTypesNotRespectedException(self.parent_node, children_type_that_are_inferior_to_minimum)

    def get_children_types_that_subceed_minimum_required(self) -> List['EducationGroupTypesEnum']:
        children_types_counter = Counter(self.parent_node.get_children_types(include_nodes_used_as_reference=True))

        result = []
        for child_type, minimum_required in self._get_minimum_child_required_by_child_type():
            if children_types_counter.get(child_type, 0) < minimum_required:
                result.append(child_type)

        return result

    def _get_minimum_child_required_by_child_type(self):
        parent_authorized_relationships = [
            relationship for relationship in self.tree.authorized_relationships.authorized_relationships
            if relationship.parent_type == self.parent_node.node_type
        ]
        return Counter([(rel.child_type, rel.min_count_authorized) for rel in parent_authorized_relationships])


class ChildTypeValidator(business_validator.BusinessValidator):
    def __init__(self, tree: 'ProgramTree', parent_node: 'Node'):
        super().__init__()
        self.tree = tree
        self.parent_node = parent_node

    def validate(self, *args, **kwargs):
        children_not_authorized = self.get_children_not_authorized()
        if children_not_authorized:
            raise ChildTypeNotAuthorizedException(self.parent_node, children_not_authorized)

    def get_children_not_authorized(self):
        children_nodes = self.parent_node.children_as_nodes_with_respect_to_reference_link
        return [children_node for children_node in children_nodes if self._is_an_invalid_child(children_node)]

    def _is_an_invalid_child(self, node: 'Node') -> bool:
        authorized_relationship = self.tree.authorized_relationships.get_authorized_relationship(
            self.parent_node.node_type,
            node.node_type
        )
        return authorized_relationship is None


class MaximumFinalitiesAuthorizedValidator(business_validator.BusinessValidator):
    def __init__(self, tree: 'ProgramTree', parent_node: 'Node'):
        super().__init__()
        self.tree = tree
        self.parent_node = parent_node

    def validate(self, *args, **kwargs):
        finalities_in_excess = self.get_finalities_exceeding_maximum_number_allowed()
        if finalities_in_excess:
            raise MaximumChildTypesReachedException(self.tree.root_node, finalities_in_excess)

    def get_finalities_exceeding_maximum_number_allowed(self) -> List["EducationGroupTypesEnum"]:
        finalities_counter = self._get_finalities_counter()
        return [
            child_type for child_type, child_number in finalities_counter.items()
            if self._is_maximum_number_surpassed(child_type, child_number)
        ]

    def _is_maximum_number_surpassed(self, children_type, number_children) -> bool:
        authorized_relationship = self.tree.authorized_relationships.get_authorized_relationship(
            self.parent_node.node_type,
            children_type
        )
        maximum_children_authorized = authorized_relationship.max_count_authorized if authorized_relationship else 0
        return number_children > maximum_children_authorized

    def _get_finalities_counter(self):
        tree_finalities = self.tree.get_all_finalities()
        return Counter([finality.node_type for finality in tree_finalities])

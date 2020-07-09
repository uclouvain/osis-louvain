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
from typing import List, Set, Tuple, Optional

from base.models.authorized_relationship import AuthorizedRelationshipList
from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType, GroupType
from base.models.enums.link_type import LinkTypes
from osis_common.ddd import interface
from osis_common.decorators.deprecated import deprecated
from program_management.ddd.business_types import *
from program_management.ddd.domain import prerequisite
from program_management.ddd.service import command
from program_management.ddd.validators._detach_root import DetachRootValidator
from program_management.ddd.validators._path_validator import PathValidator
from program_management.ddd.validators.validators_by_business_action import AttachNodeValidatorList, \
    UpdatePrerequisiteValidatorList
from program_management.ddd.validators.validators_by_business_action import DetachNodeValidatorList
from program_management.models.enums import node_type
from program_management.models.enums.node_type import NodeType

PATH_SEPARATOR = '|'
Path = str  # Example : "root|node1|node2|child_leaf"


class ProgramTreeIdentity(interface.EntityIdentity):
    def __init__(self, code: str, year: int):
        self.code = code
        self.year = year

    def __hash__(self):
        return hash(self.code + str(self.year))

    def __eq__(self, other):
        return self.code == other.code and self.year == other.year


class ProgramTree(interface.RootEntity):

    root_node = None
    authorized_relationships = None

    def __init__(self, root_node: 'Node', authorized_relationships: AuthorizedRelationshipList = None):
        self.root_node = root_node
        self.authorized_relationships = authorized_relationships
        # FIXME :: pass entity_id into the __init__ param !
        super(ProgramTree, self).__init__(entity_id=ProgramTreeIdentity(self.root_node.code, self.root_node.year))

    def __eq__(self, other: 'ProgramTree'):
        return self.root_node == other.root_node

    def is_master_2m(self):
        return self.root_node.is_master_2m()

    def is_root(self, node: 'Node'):
        return self.root_node == node

    def get_parents_using_node_as_reference(self, child_node: 'Node') -> List['Node']:
        result = []
        for tree_node in self.get_all_nodes():
            for link in tree_node.children:
                if link.child == child_node and link.is_reference():
                    result.append(link.parent)
        return result

    def get_2m_option_list(self):  # TODO :: unit tests
        tree_without_finalities = self.prune(
            ignore_children_from={GroupType.FINALITY_120_LIST_CHOICE, GroupType.FINALITY_180_LIST_CHOICE}
        )
        return tree_without_finalities.root_node.get_option_list()

    def get_parents(self, path: Path) -> List['Node']:  # TODO :: unit tests
        result = []
        str_nodes = path.split(PATH_SEPARATOR)
        if len(str_nodes) > 1:
            str_nodes = str_nodes[:-1]
            path = '{}'.format(PATH_SEPARATOR).join(str_nodes)
            result.append(self.get_node(path))
            result += self.get_parents(PATH_SEPARATOR.join(str_nodes))
        return result

    def get_links_using_node(self, child_node: 'Node') -> List['Link']:
        return [link_obj for link_obj in _links_from_root(self.root_node) if link_obj.child == child_node]

    def get_first_link_occurence_using_node(self, child_node: 'Node') -> 'Link':
        links = self.get_links_using_node(child_node)
        if links:
            return links[0]

    def get_node(self, path: Path) -> 'Node':
        """
        Return the corresponding node based on path of tree
        :param path: str
        :return: Node
        """
        try:
            return {
                str(self.root_node.pk): self.root_node,
                **self.root_node.descendents
            }[path]
        except KeyError:
            from program_management.ddd.domain import node
            raise node.NodeNotFoundException

    @deprecated  # Please use :py:meth:`~program_management.ddd.domain.program_tree.ProgramTree.get_node` instead !
    def get_node_by_id_and_type(self, node_id: int, node_type: NodeType) -> 'Node':
        """
        DEPRECATED :: Please use the :py:meth:`get_node <ProgramTree.get_node>` instead !
        Return the corresponding node based on the node_id value with respect to the class.
        :param node_id: int
        :param node_type: NodeType
        :return: Node
        """
        return next(
            (
                node for node in self.get_all_nodes()
                if node.node_id == node_id and node.type == node_type
            ),
            None
        )

    def get_node_smallest_ordered_path(self, node: 'Node') -> Optional[Path]:
        """
        Return the smallest ordered path of node inside the tree.
        The smallest ordered path would be the result of a depth-first
        search of the path of the node with respect to the order of the links.
        Meaning we will recursively search for the path node by searching
        first in the descendants of the first child and so on.
        :param node: Node
        :return: A Path if node is present in tree. None if not.
        """
        if node == self.root_node:
            return build_path(self.root_node)

        nodes_by_path = self.root_node.descendents
        return next(
            (path for path, node_obj in nodes_by_path.items() if node_obj == node),
            None
        )

    def get_node_by_code_and_year(self, code: str, year: int) -> 'Node':
        """
        Return the corresponding node based on the code and year.
        :param code: str
        :param year: int
        :return: Node
        """
        return next(
            (
                node for node in self.get_all_nodes()
                if node.code == code and node.academic_year.year == year
            ),
            None
        )

    def get_all_nodes(self, types: Set[EducationGroupTypesEnum] = None) -> Set['Node']:
        """
        Return a flat set of all nodes present in the tree
        :return: list of Node
        """
        all_nodes = set([self.root_node] + _nodes_from_root(self.root_node))
        if types:
            return set(n for n in all_nodes if n.node_type in types)
        return all_nodes

    def get_nodes_by_type(self, node_type_value) -> Set['Node']:
        return {node for node in self.get_all_nodes() if node.type == node_type_value}

    def get_nodes_that_have_prerequisites(self) -> List['NodeLearningUnitYear']:
        return list(
            sorted(
                (
                    node_obj for node_obj in self.get_nodes_by_type(node_type.NodeType.LEARNING_UNIT)
                    if node_obj.has_prerequisite
                ),
                key=lambda node_obj: node_obj.code
            )
        )

    def get_codes_permitted_as_prerequisite(self) -> List[str]:
        learning_unit_nodes_contained_in_program = self.get_nodes_by_type(node_type.NodeType.LEARNING_UNIT)
        return list(sorted(node_obj.code for node_obj in learning_unit_nodes_contained_in_program))

    def get_nodes_that_are_prerequisites(self) -> List['NodeLearningUnitYear']:  # TODO :: unit test
        return list(
            sorted(
                (
                    node_obj for node_obj in self.get_all_nodes()
                    if node_obj.is_learning_unit() and node_obj.is_prerequisite
                ),
                key=lambda node_obj: node_obj.code
            )
        )

    def count_usage(self, node: 'Node') -> int:
        return Counter(_nodes_from_root(self.root_node))[node]

    def get_all_finalities(self) -> Set['Node']:
        finality_types = set(TrainingType.finality_types_enum())
        return self.get_all_nodes(types=finality_types)

    def get_greater_block_value(self) -> int:
        all_links = self.get_all_links()
        if not all_links:
            return 0
        return max(link_obj.block_max_value for link_obj in all_links)

    def get_all_links(self) -> List['Link']:
        return _links_from_root(self.root_node)

    def get_link(self, parent: 'Node', child: 'Node') -> 'Link':
        return next((link for link in self.get_all_links() if link.parent == parent and link.child == child), None)

    def prune(self, ignore_children_from: Set[EducationGroupTypesEnum] = None) -> 'ProgramTree':
        copied_root_node = _copy(self.root_node, ignore_children_from=ignore_children_from)
        return ProgramTree(root_node=copied_root_node, authorized_relationships=self.authorized_relationships)

    def attach_node(
            self,
            node_to_attach: 'Node',
            path: Optional[Path],
            attach_command: command.AttachNodeCommand
    ) -> List['BusinessValidationMessage']:
        """
        Add a node to the tree
        :param node_to_attach: Node to add on the tree
        :param path: [Optional]The position where the node must be added
        :param attach_command: an attach node command
        """
        parent = self.get_node(path) if path else self.root_node
        path = path or str(self.root_node.node_id)
        link_type = attach_command.link_type
        block = attach_command.block
        is_valid, messages = self.clean_attach_node(node_to_attach, path, link_type, block)
        if is_valid:
            parent.add_child(
                node_to_attach,
                access_condition=attach_command.access_condition,
                is_mandatory=attach_command.is_mandatory,
                block=attach_command.block,
                link_type=attach_command.link_type,
                comment=attach_command.comment,
                comment_english=attach_command.comment_english,
                relative_credits=attach_command.relative_credits
            )
        return messages

    def clean_attach_node(
            self,
            node_to_attach: 'Node',
            path: Path,
            link_type: Optional[LinkTypes],
            block: Optional[int]
    ) -> Tuple[bool, List['BusinessValidationMessage']]:
        validator = AttachNodeValidatorList(self, node_to_attach, path, link_type, block)
        return validator.is_valid(), validator.messages

    def set_prerequisite(
            self,
            prerequisite_expression: 'PrerequisiteExpression',
            node: 'NodeLearningUnitYear'
    ) -> List['BusinessValidationMessage']:
        """
        Set prerequisite for the node corresponding to the path.
        """
        is_valid, messages = self.clean_set_prerequisite(prerequisite_expression, node)
        if is_valid:
            node.set_prerequisite(
                prerequisite.factory.from_expression(prerequisite_expression, self.root_node.year)
            )
        return messages

    def clean_set_prerequisite(
            self,
            prerequisite_expression: 'PrerequisiteExpression',
            node: 'NodeLearningUnitYear'
    ) -> (bool, List['BusinessValidationMessage']):
        validator = UpdatePrerequisiteValidatorList(prerequisite_expression, node, self)
        return validator.is_valid(), validator.messages

    def detach_node(self, path_to_node_to_detach: Path) -> Tuple[bool, List['BusinessValidationMessage']]:
        """
        Detach a node from tree
        :param path_to_node_to_detach: The path node to detach
        :return:
        """
        validator = PathValidator(path_to_node_to_detach)
        if not validator.is_valid():
            return False, validator.messages

        validator = DetachRootValidator(self, path_to_node_to_detach)
        if not validator.is_valid():
            return False, validator.messages

        parent_path, *__ = path_to_node_to_detach.rsplit(PATH_SEPARATOR, 1)
        parent = self.get_node(parent_path)
        node_to_detach = self.get_node(path_to_node_to_detach)
        is_valid, messages = self.clean_detach_node(node_to_detach, parent_path)
        if is_valid:
            self.remove_prerequisites(node_to_detach)
            parent.detach_child(node_to_detach)
        return is_valid, messages

    def remove_prerequisites(self, detached_node: 'Node'):
        if detached_node.is_learning_unit():
            to_remove = [detached_node] if detached_node.has_prerequisite else []
        else:
            to_remove = ProgramTree(root_node=detached_node).get_nodes_that_have_prerequisites()
        for n in to_remove:
            n.remove_all_prerequisite_items()

    def clean_detach_node(
            self,
            node_to_detach: 'Node',
            path_to_parent: Path
    ) -> Tuple[bool, List['BusinessValidationMessage']]:
        validator = DetachNodeValidatorList(self, node_to_detach, path_to_parent)
        return validator.is_valid(), validator.messages


def _nodes_from_root(root: 'Node') -> List['Node']:
    nodes = [root]
    for link in root.children:
        nodes.extend(_nodes_from_root(link.child))
    return nodes


def _links_from_root(root: 'Node', ignore: Set[EducationGroupTypesEnum] = None) -> List['Link']:
    links = []
    for link in root.children:
        if not ignore or link.parent.node_type not in ignore:
            links.append(link)
            links.extend(_links_from_root(link.child, ignore=ignore))
    return links


def build_path(*nodes):
    return '{}'.format(PATH_SEPARATOR).join((str(n.node_id) for n in nodes))


def _copy(root: 'Node', ignore_children_from: Set[EducationGroupTypesEnum] = None):
    new_node = _deepcopy_node_without_copy_children_recursively(root)
    new_children = []
    for link in root.children:
        if ignore_children_from and link.parent.node_type in ignore_children_from:
            continue
        new_child = _copy(link.child, ignore_children_from=ignore_children_from)
        new_link = _deepcopy_link_without_copy_children_recursively(link)
        new_link.child = new_child
        new_children.append(new_link)
    new_node.children = new_children
    return new_node


def _deepcopy_node_without_copy_children_recursively(original_node: 'Node'):
    original_children = original_node.children
    original_node.children = []  # To avoid recursive deep copy of all children behind
    copied_node = copy.deepcopy(original_node)
    original_node.children = original_children
    return copied_node


def _deepcopy_link_without_copy_children_recursively(original_link: 'Link'):
    original_child = original_link.child
    original_link.child = None  # To avoid recursive deep copy of all children behind
    new_link = copy.deepcopy(original_link)
    original_link.child = original_child
    return new_link

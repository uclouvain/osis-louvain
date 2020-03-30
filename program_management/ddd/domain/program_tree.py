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
from typing import List, Set

from base.models.authorized_relationship import AuthorizedRelationshipList
from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType
from program_management.ddd.business_types import *
from program_management.ddd.validators.validators_by_business_action import AttachNodeValidatorList
from program_management.models.enums import node_type

PATH_SEPARATOR = '|'
Path = str  # Example : "root|node1|node2|child_leaf"


class ProgramTree:

    root_node = None
    authorized_relationships = None

    def __init__(self, root_node: 'Node', authorized_relationships: AuthorizedRelationshipList = None):
        self.root_node = root_node
        self.authorized_relationships = authorized_relationships

    def __eq__(self, other):
        return self.root_node == other.root_node

    def is_master_2m(self):
        return self.root_node.is_master_2m()

    def get_parents_using_node_as_reference(self, child_node: 'Node') -> List['Node']:
        result = []
        for tree_node in self.get_all_nodes():
            for link in tree_node.children:
                if link.child == child_node and link.is_reference():
                    result.append(link.parent)
        return result

    def get_parents(self, path: Path) -> List['Node']:
        result = []
        str_nodes = path.split(PATH_SEPARATOR)
        if len(str_nodes) > 1:
            str_nodes = str_nodes[:-1]
            path = '{}'.format(PATH_SEPARATOR).join(str_nodes)
            result.append(self.get_node(path))
            result += self.get_parents(PATH_SEPARATOR.join(str_nodes))
        return result

    def get_links(self):
        return _links_from_root(self.root_node)

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

    def get_node_by_id_and_class(self, node_id: int, node_class: 'Node') -> 'Node':
        """
        Return the corresponding node based on the node_id value with respect to the class.
        :param node_id: int
        :param node_class: a Node subclass
        :return: Node
        """
        return next(
            (
                node for node in self.get_all_nodes()
                if node.node_id == node_id and isinstance(node, node_class)
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

    def get_nodes_by_type(self, node_type_value) -> List['Node']:
        return [node for node in self.get_all_nodes() if node.type == node_type_value]

    def get_codes_permitted_as_prerequisite(self):
        learning_unit_nodes_contained_in_program = self.get_nodes_by_type(node_type.NodeType.LEARNING_UNIT)
        return [node_obj.code for node_obj in learning_unit_nodes_contained_in_program]

    # TODO :: unit test
    def get_all_finalities(self):
        finality_types = set(TrainingType.finality_types_enum())
        return self.get_all_nodes(types=finality_types)

    def get_greater_block_value(self):
        all_links = self.get_all_links()
        if not all_links:
            return 0
        return max(l.block_max_value for l in all_links)

    def get_all_links(self) -> List['Link']:
        return _links_from_root(self.root_node)

    def prune(self, ignore_children_from: Set[EducationGroupTypesEnum] = None) -> 'ProgramTree':
        copied_root_node = _copy(self.root_node, ignore_children_from=ignore_children_from)
        return ProgramTree(root_node=copied_root_node, authorized_relationships=self.authorized_relationships)

    def attach_node(self, node_to_attach: 'Node', path: Path = None, **link_attributes):
        """
        Add a node to the tree
        :param node_to_attach: Node to add on the tree
        :param path: [Optional] The position where the node must be added
        """
        parent = self.get_node(path) if path else self.root_node
        path = path or str(self.root_node.node_id)
        is_valid, messages = self.clean_attach_node(node_to_attach, path)
        if is_valid:
            parent.add_child(node_to_attach, **link_attributes)
        return messages

    def clean_attach_node(self, node_to_attach: 'Node', path: Path):
        validator = AttachNodeValidatorList(self, node_to_attach, path)
        return validator.is_valid(), validator.messages

    def detach_node(self, path: str):
        """
        Detach a node from tree
        :param path: The path node to detach
        :return:
        """
        parent_path, *node_id = path.rsplit(PATH_SEPARATOR, 1)
        parent = self.get_node(parent_path)
        if not node_id:
            raise Exception("You cannot detach root node")
        parent.detach_child(node_id)


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

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
from typing import List, Set, Optional

import attr

from base.models.authorized_relationship import AuthorizedRelationshipList
from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType, GroupType, MiniTrainingType
from base.models.enums.link_type import LinkTypes
from osis_common.ddd import interface
from osis_common.decorators.deprecated import deprecated
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain.node import factory as node_factory, NodeIdentity, Node
from program_management.ddd.domain.link import factory as link_factory
from program_management.ddd.domain import prerequisite, exception
from program_management.ddd.domain.service.generate_node_abbreviated_title import GenerateNodeAbbreviatedTitle
from program_management.ddd.domain.service.generate_node_code import GenerateNodeCode
from program_management.ddd.domain.service.validation_rule import FieldValidationRule
from program_management.ddd.repositories import load_authorized_relationship
from program_management.ddd.validators import validators_by_business_action
from program_management.ddd.validators._path_validator import PathValidator
from program_management.models.enums import node_type
from program_management.models.enums.node_type import NodeType
from education_group.ddd.business_types import *

PATH_SEPARATOR = '|'
Path = str  # Example : "root|node1|node2|child_leaf"


@attr.s(frozen=True, slots=True)
class ProgramTreeIdentity(interface.EntityIdentity):
    code = attr.ib(type=str)
    year = attr.ib(type=int)


class ProgramTreeBuilder:

    def copy_to_next_year(self, copy_from: 'ProgramTree', repository: 'ProgramTreeRepository') -> 'ProgramTree':
        identity_next_year = attr.evolve(copy_from.entity_id, year=copy_from.entity_id.year + 1)
        try:
            program_tree_next_year = repository.get(identity_next_year)
            # Case update program tree to next year
            # TODO :: To implement in OSIS-4809
            pass
        except exception.ProgramTreeNotFoundException:
            # Case create program tree to next year
            program_tree_next_year = attr.evolve(  # Copy to new object
                copy_from,
                root_node=self._copy_node_and_children_to_next_year(copy_from.root_node),
                entity_id=identity_next_year,
            )
        return program_tree_next_year

    def _copy_node_and_children_to_next_year(self, copy_from_node: 'Node') -> 'Node':
        parent_next_year = node_factory.copy_to_next_year(copy_from_node)
        links_next_year = []
        for copy_from_link in copy_from_node.children:
            child_node = copy_from_link.child
            child_next_year = self._copy_node_and_children_to_next_year(child_node)
            link_next_year = link_factory.copy_to_next_year(copy_from_link, parent_next_year, child_next_year)
            parent_next_year.children.append(link_next_year)
            links_next_year.append(link_next_year)
        return parent_next_year

    def build_from_orphan_group_as_root(
            self,
            orphan_group_as_root: 'Group',
            node_repository: 'NodeRepository'
    ) -> 'ProgramTree':
        root_node = node_repository.get(NodeIdentity(code=orphan_group_as_root.code, year=orphan_group_as_root.year))
        program_tree = ProgramTree(root_node=root_node, authorized_relationships=load_authorized_relationship.load())
        self._generate_mandatory_direct_children(program_tree=program_tree)
        return program_tree

    def _generate_mandatory_direct_children(
            self,
            program_tree: 'ProgramTree'
    ) -> List['Node']:
        children = []
        root_node = program_tree.root_node
        for child_type in program_tree.get_ordered_mandatory_children_types(program_tree.root_node):
            generated_child_title = FieldValidationRule.get(
                child_type,
                'title_fr'
            ).initial_value
            child = node_factory.get_node(
                type=NodeType.GROUP,
                node_type=child_type,
                code=GenerateNodeCode.generate_from_parent_node(root_node, child_type),
                title=GenerateNodeAbbreviatedTitle.generate(
                    parent_node=root_node,
                    child_node_type=child_type,
                ),
                year=root_node.year,
                teaching_campus=root_node.teaching_campus,
                management_entity_acronym=root_node.management_entity_acronym,
                group_title_fr="{child_title} {parent_abbreviated_title}".format(
                    child_title=generated_child_title,
                    parent_abbreviated_title=root_node.title
                ),
                start_year=root_node.year,
            )
            child._has_changed = True
            root_node.add_child(child, is_mandatory=True)
            children.append(child)
        return children


@attr.s(slots=True)
class ProgramTree(interface.RootEntity):

    root_node = attr.ib(type=Node)
    authorized_relationships = attr.ib(type=AuthorizedRelationshipList, factory=list)
    entity_id = attr.ib(type=ProgramTreeIdentity)  # FIXME :: pass entity_id as mandatory param !

    @entity_id.default
    def _entity_id(self) -> 'ProgramTreeIdentity':
        return ProgramTreeIdentity(self.root_node.code, self.root_node.year)

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

    def get_all_mini_training(self) -> Set['Node']:
        mini_training_types = set(MiniTrainingType.mini_training_types_enum())
        return self.get_all_nodes(types=mini_training_types)

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

    def get_ordered_mandatory_children_types(self, parent_node: 'Node') -> List[EducationGroupTypesEnum]:
        return self.authorized_relationships.get_ordered_mandatory_children_types(parent_node.node_type)

    def paste_node(
            self,
            node_to_paste: 'Node',
            paste_command: command.PasteElementCommand,
            tree_repository: 'ProgramTreeRepository'
    ) -> 'Link':
        """
        Add a node to the tree
        :param node_to_paste: Node to paste into the tree
        :param paste_command: a paste node command
        :param tree_repository: a tree repository
        :return: the created link
        """
        validator = validators_by_business_action.PasteNodeValidatorList(
            self,
            node_to_paste,
            paste_command,
            tree_repository
        )
        validator.validate()

        path_to_paste_to = paste_command.path_where_to_paste
        node_to_paste_to = self.get_node(path_to_paste_to)
        return node_to_paste_to.add_child(
                node_to_paste,
                access_condition=paste_command.access_condition,
                is_mandatory=paste_command.is_mandatory,
                block=paste_command.block,
                link_type=paste_command.link_type,
                comment=paste_command.comment,
                comment_english=paste_command.comment_english,
                relative_credits=paste_command.relative_credits
        )

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
        validator = validators_by_business_action.UpdatePrerequisiteValidatorList(prerequisite_expression, node, self)
        return validator.is_valid(), validator.messages

    def detach_node(self, path_to_node_to_detach: Path, tree_repository: 'ProgramTreeRepository') -> 'Link':
        """
        Detach a node from tree
        :param path_to_node_to_detach: The path node to detach
        :param tree_repository: a tree repository
        :return: the suppressed link
        """
        PathValidator(path_to_node_to_detach).validate()

        node_to_detach = self.get_node(path_to_node_to_detach)
        parent_path, *__ = path_to_node_to_detach.rsplit(PATH_SEPARATOR, 1)
        validators_by_business_action.DetachNodeValidatorList(
            self,
            node_to_detach,
            parent_path,
            tree_repository
        ).validate()

        self.remove_prerequisites(node_to_detach, parent_path)
        parent = self.get_node(parent_path)
        return parent.detach_child(node_to_detach)

    def __copy__(self) -> 'ProgramTree':
        return ProgramTree(root_node=_copy(self.root_node))

    def remove_prerequisites(self, detached_node: 'Node', parent_path):
        pruned_tree = ProgramTree(root_node=_copy(self.root_node))
        pruned_tree.get_node(parent_path).detach_child(detached_node)
        pruned_tree_children = pruned_tree.get_all_nodes()

        if detached_node.is_learning_unit():
            to_remove = [detached_node] if detached_node.has_prerequisite else []
        else:
            to_remove = ProgramTree(root_node=detached_node).get_nodes_that_have_prerequisites()

        for n in to_remove:
            if n not in pruned_tree_children:
                n.remove_all_prerequisite_items()

    def get_relative_credits_values(self, child_node: 'NodeIdentity'):
        distinct_credits_repr = []
        node = self.get_node_by_code_and_year(child_node.code, child_node.year)

        for link_obj in self.get_links_using_node(node):
            if link_obj.relative_credits_repr not in distinct_credits_repr:
                distinct_credits_repr.append(link_obj.relative_credits_repr)
        return " ; ".join(
            set(["{}".format(credits) for credits in distinct_credits_repr])
        )

    def get_blocks_values(self, child_node: 'NodeIdentity'):
        node = self.get_node_by_code_and_year(child_node.code, child_node.year)
        return " ; ".join(
            [str(grp.block) for grp in self.get_links_using_node(node) if grp.block]
        )

    def is_empty(self):
        """
        Check if tree is empty.
        An empty tree is defined as a tree with other link than mandatory groups
        """
        nodes = self.get_all_nodes()
        for node in nodes:
            counter_direct_children = Counter(node.get_children_types(include_nodes_used_as_reference=True))
            counter_mandatory_direct_children = Counter(self.get_ordered_mandatory_children_types(node))

            if counter_direct_children - counter_mandatory_direct_children:
                return False
        return True

    def update_link(
            self,
            parent_path: Path,
            child_id: 'NodeIdentity',
            relative_credits: int,
            access_condition: bool,
            is_mandatory: bool,
            block: int,
            link_type: str,
            comment: str,
            comment_english: str
    ) -> 'Link':
        """
        Update link's attributes between parent_path and child_node
        :param parent_path: The parent path node
        :param child_id: The identity of child node
        :param relative_credits: The link's relative credits
        :param access_condition: The link's access_condition
        :param is_mandatory: The link's is_mandatory
        :param block: The block of link
        :param link_type: The type of link
        :param comment: The comment of link
        :param comment_english: The comment english of link
        :return: Updated link
        """
        parent_node = self.get_node(parent_path)
        child_node = parent_node.get_direct_child_as_node(child_id)

        link_updated = parent_node.update_link_of_direct_child_node(
            child_id,
            relative_credits=relative_credits,
            access_condition=access_condition,
            is_mandatory=is_mandatory,
            block=block,
            link_type=link_type,
            comment=comment,
            comment_english=comment_english
        )

        validators_by_business_action.UpdateLinkValidatorList(
            parent_node,
            child_node,
            link_updated
        ).validate()
        return link_updated


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

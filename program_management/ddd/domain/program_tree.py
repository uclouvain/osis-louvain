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
import collections
import copy
import itertools
from collections import Counter
from typing import List, Set, Optional, Dict

import attr

from base.ddd.utils.converters import to_upper_case_converter
from base.models.authorized_relationship import AuthorizedRelationshipList
from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType, GroupType
from base.models.enums.link_type import LinkTypes
from base.utils.cache import cached_result
from education_group.ddd.business_types import *
from osis_common.ddd import interface
from osis_common.decorators.deprecated import deprecated
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.command import DO_NOT_OVERRIDE, UpdateLinkCommand
from program_management.ddd.domain import exception, report_events
from program_management.ddd.domain.link import factory as link_factory, LinkBuilder
from program_management.ddd.domain.node import factory as node_factory, NodeIdentity, Node, NodeNotFoundException
from program_management.ddd.domain.prerequisite import Prerequisites, \
    PrerequisitesBuilder
from program_management.ddd.domain.report import Report
from program_management.ddd.domain.service.generate_node_code import GenerateNodeCode
from program_management.ddd.repositories import load_authorized_relationship
from program_management.ddd.validators import validators_by_business_action
from program_management.ddd.validators._path_validator import PathValidator
from program_management.models.enums.node_type import NodeType

PATH_SEPARATOR = '|'
Path = str  # Example : "root|node1|node2|child_leaf"


@attr.s(frozen=True, slots=True)
class ProgramTreeIdentity(interface.EntityIdentity):
    code = attr.ib(type=str, converter=to_upper_case_converter)
    year = attr.ib(type=int)


class ProgramTreeBuilder:

    def create_and_fill_from_program_tree(
            self,
            duplicate_from: 'ProgramTree',
            transition_name: str,
            override_end_year_to: int = DO_NOT_OVERRIDE,
            override_start_year_to: int = None
    ) -> 'ProgramTree':
        """
        Generates new program tree with new nodes and links based on attributes of 'duplicate_from' program tree.
        :param duplicate_from: The program tree from which are copied attributes in the new one.
        :param override_end_year_to: This param override the 'end year' of all nodes and links in the Tree.
        :param override_start_year_to: This param override the 'start year' of all nodes and links in the Tree.
        :return:
        """
        copied_root = self._create_and_fill_root_and_direct_children(
            duplicate_from,
            transition_name,
            override_end_year_to=override_end_year_to,
            override_start_year_to=override_start_year_to
        )
        copied_tree = attr.evolve(  # Copy to new object
            duplicate_from,
            root_node=copied_root,
            entity_id=ProgramTreeIdentity(code=copied_root.code, year=copied_root.year),
        )
        return copied_tree

    def _create_and_fill_root_and_direct_children(
            self,
            program_tree: 'ProgramTree',
            transition_name: str,
            override_end_year_to: int = DO_NOT_OVERRIDE,
            override_start_year_to: int = DO_NOT_OVERRIDE
    ) -> 'Node':
        root_node = program_tree.root_node
        new_code = GenerateNodeCode().generate_from_parent_node(
            parent_node=root_node,
            child_node_type=root_node.node_type,
            duplicate_to_transition=bool(transition_name)
        )
        new_parent = node_factory.create_and_fill_from_node(
            create_from=root_node,
            new_code=new_code,
            override_end_year_to=override_end_year_to,
            override_start_year_to=override_start_year_to,
            transition_name=transition_name
        )
        mandatory_children_types = program_tree.get_ordered_mandatory_children_types(program_tree.root_node)
        for copy_from_link in [n for n in root_node.children if n.child.node_type in mandatory_children_types]:
            child_node = copy_from_link.child
            new_code = GenerateNodeCode().generate_from_parent_node(
                parent_node=child_node,
                child_node_type=child_node.node_type,
                duplicate_to_transition=bool(transition_name)
            )
            new_child = node_factory.create_and_fill_from_node(
                create_from=child_node,
                new_code=new_code,
                override_end_year_to=override_end_year_to,
                override_start_year_to=override_start_year_to,
            )
            copied_link = link_factory.create_link(new_parent, new_child)
            new_parent.children.append(copied_link)
        return new_parent

    def copy_to_next_year(self, copy_from: 'ProgramTree', repository: 'ProgramTreeRepository') -> 'ProgramTree':
        validators_by_business_action.CopyProgramTreeValidatorList(copy_from).validate()
        identity_next_year = attr.evolve(copy_from.entity_id, year=copy_from.entity_id.year + 1)
        try:
            # Case update program tree to next year
            program_tree_next_year = repository.get(identity_next_year)
        except exception.ProgramTreeNotFoundException:
            # Case create program tree to next year
            root_next_year = node_factory.copy_to_next_year(copy_from.root_node)
            program_tree_next_year = ProgramTree(
                entity_id=identity_next_year,
                root_node=root_next_year,
                authorized_relationships=load_authorized_relationship.load()
            )

        root_next_year = program_tree_next_year.root_node
        mandatory_types = copy_from.get_ordered_mandatory_children_types(
            parent_node=root_next_year
        )
        children_current_year = copy_from.root_node.get_direct_children_as_nodes()
        for child_current_year in children_current_year:
            if child_current_year.node_type in mandatory_types:
                child_next_year = node_factory.copy_to_next_year(child_current_year)
                root_next_year.add_child(child_next_year, is_mandatory=True)
        return program_tree_next_year

    def copy_prerequisites_from_program_tree(self, from_tree: 'ProgramTree', to_tree: 'ProgramTree') -> 'ProgramTree':
        to_tree.prerequisites = PrerequisitesBuilder().copy_to_tree(from_tree.prerequisites, to_tree)
        return to_tree

    def fill_from_last_year_program_tree(
            self,
            last_year_tree: 'ProgramTree',
            to_tree: 'ProgramTree',
            existing_nodes: Set['Node'],
    ) -> 'ProgramTree':
        validators_by_business_action.FillProgramTreeValidatorList(to_tree).validate()

        self._fill_node_from_last_year_node(last_year_tree.root_node, to_tree.root_node, existing_nodes, to_tree)

        return to_tree

    def _fill_node_from_last_year_node(
            self,
            last_year_node: 'Node',
            to_node: 'Node',
            existing_nodes: Set['Node'],
            to_tree: 'ProgramTree'
    ) -> 'Node':
        links_to_copy = (
            link for link in last_year_node.children
            if self._can_link_be_copied_with_respect_to_child_end_date(link, to_node.year)
        )
        links_that_cannot_be_copied = (
            link for link in last_year_node.children
            if not self._can_link_be_copied_with_respect_to_child_end_date(link, to_node.year)
        )
        for link in links_that_cannot_be_copied:
            to_tree.report.add_warning(
                report_events.NotCopyTrainingMiniTrainingNotExistForYearEvent(
                    node=link.child,
                    end_year=link.child.end_academic_year,
                    copy_year=to_node.academic_year
                )
            )

        for last_year_link in links_to_copy:
            child_node_identity = attr.evolve(last_year_link.child.entity_id, year=to_node.year)
            child = self._get_existing_node(existing_nodes, child_node_identity)

            if last_year_link.child.is_learning_unit() and not child:
                child = last_year_link.child
                to_tree.report.add_warning(
                    report_events.CopyLearningUnitNotExistForYearEvent(
                        code=child.code,
                        copy_year=to_node.year,
                        year=child.year
                    )
                )
            elif last_year_link.child.is_group() and not child:
                child = child or node_factory.copy_to_next_year(last_year_link.child)

            elif not child:
                to_tree.report.add_warning(
                    report_events.NotCopyTrainingMiniTrainingNotExistingEvent(
                        node=last_year_link.child,
                        copy_year=to_node.academic_year
                    )
                )
                continue

            copied_link = LinkBuilder().from_link(last_year_link, to_node, child)
            to_node.children.append(copied_link)

            if self._can_link_child_be_filled(copied_link, to_tree.authorized_relationships):
                self._fill_node_from_last_year_node(last_year_link.child, child, existing_nodes, to_tree)
            elif copied_link.is_reference() and is_empty(copied_link.child, to_tree.authorized_relationships) and\
                    copied_link.child.is_group():
                to_tree.report.add_warning(
                    report_events.CopyReferenceGroupEvent(node=last_year_link.child)
                )
            elif copied_link.is_reference() and is_empty(copied_link.child, to_tree.authorized_relationships):
                to_tree.report.add_warning(
                    report_events.CopyReferenceEmptyEvent(node=last_year_link.child)
                )
            elif not is_empty(copied_link.child, to_tree.authorized_relationships) and \
                    not copied_link.child.is_training_formation_root():
                to_tree.report.add_warning(
                    report_events.NodeAlreadyCopiedEvent(node=last_year_link.child, copy_year=to_node.academic_year)
                )

        return to_node

    def fill_transition_from_program_tree(
            self,
            from_tree: 'ProgramTree',
            to_tree: 'ProgramTree',
            existing_nodes: Set['Node'],
            node_code_generator: 'GenerateNodeCode'
    ) -> 'ProgramTree':
        validators_by_business_action.FillTransitionProgramTreeValidatorList(
            from_tree,
            to_tree,
            existing_nodes
        ).validate()

        self._fill_node_from_node_in_case_of_transition(
            from_tree.root_node,
            to_tree.root_node,
            to_tree.authorized_relationships,
            existing_nodes,
            to_tree.root_node.transition_name,
            node_code_generator,
            to_tree
        )

        return to_tree

    def _fill_node_from_node_in_case_of_transition(
            self,
            from_node: 'Node',
            to_node: 'Node',
            relationships: 'AuthorizedRelationshipList',
            existing_nodes: Set['Node'],
            transition_name: 'str',
            node_code_generator: 'GenerateNodeCode',
            to_tree: 'ProgramTree'
    ) -> 'Node':
        links_to_copy = (
            link for link in from_node.children
            if self._can_link_be_copied_with_respect_to_child_end_date(link, to_node.year)
        )
        links_that_cannot_be_copied = (
            link for link in from_node.children
            if not self._can_link_be_copied_with_respect_to_child_end_date(link, to_node.year)
        )
        for link in links_that_cannot_be_copied:
            to_tree.report.add_warning(
                report_events.NotCopyTrainingMiniTrainingNotExistForYearEvent(
                    node=link.child,
                    end_year=link.child.end_academic_year,
                    copy_year=to_node.academic_year
                )
            )

        for source_link in links_to_copy:
            child_node_identity = attr.evolve(source_link.child.entity_id, year=to_node.year)

            child = self._get_existing_node(existing_nodes, child_node_identity)

            if source_link.child.is_learning_unit() and not child:
                child = source_link.child
                to_tree.report.add_warning(
                    report_events.CopyLearningUnitNotExistForYearEvent(
                        code=child.code,
                        copy_year=to_node.year,
                        year=child.year
                    )
                )
            elif relationships.is_mandatory_child(source_link.parent.node_type, source_link.child.node_type):
                child = self._get_equivalent_mandatory_child(
                    to_node.children_as_nodes,
                    source_link.child.node_type
                )
            elif source_link.child.is_group():
                new_code = node_code_generator.generate_transition_code(source_link.child.code)
                child = node_factory.copy_to_year(source_link.child, to_node.year, new_code)
            elif source_link.child.is_training():
                child = self._get_existing_transition_node(
                    existing_nodes,
                    source_link.child,
                    to_node.year,
                    transition_name
                )
            if not child and source_link.child.is_training():
                to_tree.report.add_warning(
                    report_events.CopyTransitionTrainingNotExistingEvent(
                        root_node=to_tree.root_node,
                        node=source_link.child,
                    )
                )
                continue
            elif not child:
                to_tree.report.add_warning(
                    report_events.NotCopyTrainingMiniTrainingNotExistingEvent(
                        node=source_link.child,
                        copy_year=to_node.academic_year
                    )
                )
                continue

            copied_link = LinkBuilder().from_link(source_link, to_node, child)
            if copied_link.child.is_group() and copied_link.is_reference():
                copied_link.link_type = None
            to_node.children.append(copied_link)

            if self._can_link_child_be_filled(copied_link, relationships):
                if copied_link.child.is_option():
                    self._fill_node_from_last_year_node(
                        source_link.child,
                        child,
                        existing_nodes,
                        to_tree
                    )
                else:
                    self._fill_node_from_node_in_case_of_transition(
                        source_link.child,
                        child,
                        relationships,
                        existing_nodes,
                        transition_name,
                        node_code_generator,
                        to_tree
                    )
            elif copied_link.is_reference() and is_empty(copied_link.child, to_tree.authorized_relationships) \
                    and copied_link.child.is_group():
                to_tree.report.add_warning(
                    report_events.CopyReferenceGroupEvent(node=copied_link.child)
                )
            elif copied_link.is_reference() and is_empty(copied_link.child, to_tree.authorized_relationships):
                to_tree.report.add_warning(
                    report_events.CopyReferenceEmptyEvent(node=copied_link.child)
                )
            elif not is_empty(copied_link.child, to_tree.authorized_relationships) and \
                    not copied_link.child.is_training_formation_root():
                to_tree.report.add_warning(
                    report_events.NodeAlreadyCopiedEvent(node=copied_link.child, copy_year=to_node.academic_year)
                )

        return to_node

    def _get_existing_node(self, existing_nodes: Set['Node'], node_id: 'NodeIdentity') -> Optional['Node']:
        return next((node for node in existing_nodes if node.entity_id == node_id), None)

    def _get_equivalent_mandatory_child(
            self,
            children: List['Node'],
            child_type: 'EducationGroupTypesEnum'
    ) -> Optional['Node']:
        return next((child for child in children if child.node_type == child_type), None)

    def _get_existing_transition_node(
            self,
            existing_nodes: Set['Node'],
            other_node: 'Node',
            year: int,
            transition_name: str
    ) -> Optional['Node']:
        return next((
                node for node in existing_nodes
                if not node.is_learning_unit() and node.is_transition_node_equivalent(other_node, transition_name, year)
            ),
            None
        )

    def _can_link_be_copied_with_respect_to_child_end_date(self, link: 'Link', year_to_be_copied_to: int) -> bool:
        is_child_end_date_superior_or_equal_to_year_to_be_copied_to = \
            not link.child.end_date or link.child.end_date >= year_to_be_copied_to

        if is_child_end_date_superior_or_equal_to_year_to_be_copied_to:
            return True
        elif link.child.is_group():
            return True
        elif link.child.is_learning_unit():
            return True
        return False

    def _can_link_child_be_filled(self, link: 'Link', relationships: 'AuthorizedRelationshipList') -> bool:
        if link.child.is_learning_unit():
            return False
        elif link.is_reference():
            return False
        elif is_empty(link.child, relationships):
            return True
        elif relationships.is_mandatory_child(link.parent.node_type, link.child.node_type):
            return True
        return False

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
            program_tree: 'ProgramTree',
    ) -> List['Node']:
        children = []
        root_node = program_tree.root_node
        for child_type in program_tree.get_ordered_mandatory_children_types(program_tree.root_node):
            child = node_factory.generate_from_parent(parent_node=root_node, child_type=child_type)
            root_node.add_child(child, is_mandatory=True)
            children.append(child)
        return children


@attr.s(slots=True, hash=False, eq=False)
class ProgramTree(interface.RootEntity):

    root_node = attr.ib(type=Node)
    authorized_relationships = attr.ib(type='AuthorizedRelationshipList', factory=list)
    entity_id = attr.ib(type=ProgramTreeIdentity)  # FIXME :: pass entity_id as mandatory param !
    prerequisites = attr.ib(type='Prerequisites')
    report = attr.ib(type=Optional[Report], default=None)  # type: Report

    @property
    def year(self) -> int:
        return self.entity_id.year

    @prerequisites.default
    def _default_prerequisite(self) -> 'Prerequisites':
        from program_management.ddd.domain.prerequisite import NullPrerequisites
        return NullPrerequisites()

    def is_empty(self, parent_node=None):
        return is_empty(parent_node or self.root_node, self.authorized_relationships)

    @entity_id.default
    def _entity_id(self) -> 'ProgramTreeIdentity':
        return ProgramTreeIdentity(self.root_node.code, self.root_node.year)

    def is_master_2m(self):
        return self.root_node.is_master_2m()

    def is_bachelor(self) -> bool:
        return self.root_node.is_bachelor()

    def is_root(self, node: 'Node'):
        return self.root_node == node

    def is_used_only_inside_minor_or_deepening(self, node: 'Node') -> bool:
        usages = []
        for path in self.search_paths_using_node(node):
            inside_minor_or_deepening = any(p for p in self.get_parents(path) if p.is_minor_or_deepening())
            usages.append(inside_minor_or_deepening)
        return all(usages)

    def allows_learning_unit_child(self, node: 'Node') -> bool:
        try:
            return self.authorized_relationships.is_authorized(
                parent_type=node.node_type,
                child_type=NodeType.LEARNING_UNIT,
            )
        except AttributeError:
            return False

    def get_parents_node_with_respect_to_reference(self, parent_node: 'Node') -> List['Node']:
        links = _links_from_root(self.root_node)

        def _get_parents(child_node: 'Node') -> List['Node']:
            result = []
            reference_links = [link_obj for link_obj in links
                               if link_obj.child == child_node and link_obj.is_reference()]
            for link_obj in reference_links:
                reference_parents = _get_parents(link_obj.parent)
                if reference_parents:
                    result.extend(reference_parents)
                else:
                    result.append(link_obj.parent)
            return result

        non_reference_links = [link_obj for link_obj in links
                               if link_obj.child == parent_node and not link_obj.is_reference()]
        if non_reference_links or self.root_node == parent_node:
            return [parent_node] + _get_parents(parent_node)
        return _get_parents(parent_node)

    def get_all_parents(self, child_node: 'Node') -> Set['Node']:
        paths_using_node = self.search_paths_using_node(child_node)
        return set(
            itertools.chain.from_iterable(self.get_parents(path) for path in paths_using_node)
        )

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
            path = PATH_SEPARATOR.join(str_nodes)
            result.append(self.get_node(path))
            result += self.get_parents(PATH_SEPARATOR.join(str_nodes))
        return result

    def get_mandatory_children(self, parent_node: 'Node'):
        return [
            node for node in parent_node.children_as_nodes
            if node.node_type in self.authorized_relationships.get_ordered_mandatory_children_types(
                parent_node.node_type
            )
        ]

    def search_links_using_node(self, child_node: 'Node') -> List['Link']:
        return [link_obj for link_obj in self.get_all_links() if link_obj.child == child_node]

    def get_first_link_occurence_using_node(self, child_node: 'Node') -> 'Link':
        links = self.search_links_using_node(child_node)
        if links:
            return links[0]

    def get_node(self, path: Path) -> 'Node':
        """
        Return the corresponding node based on path of tree
        :param path: str
        :return: Node
        """

        def _get_node(root_node: 'Node', path: 'Path') -> 'Node':
            direct_child_id, separator, remaining_path = path.partition(PATH_SEPARATOR)
            direct_child = next(child for child in root_node.children_as_nodes if str(child.pk) == direct_child_id)

            if not remaining_path:
                return direct_child
            return _get_node(direct_child, remaining_path)

        try:
            if path == str(self.root_node.pk):
                return self.root_node
            return _get_node(self.root_node, path.split(PATH_SEPARATOR, maxsplit=1)[1])
        except (StopIteration, IndexError):
            raise NodeNotFoundException

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

    def get_all_learning_unit_nodes(self) -> List['NodeLearningUnitYear']:
        return self.root_node.get_all_children_as_learning_unit_nodes()

    def get_nodes_permitted_as_prerequisite(self) -> List['NodeLearningUnitYear']:
        nodes_permitted = set()
        for node in self.get_all_learning_unit_nodes():
            if self.is_bachelor() and self.is_used_only_inside_minor_or_deepening(node):
                continue
            nodes_permitted.add(node)
        return list(sorted(nodes_permitted, key=lambda n: n.code))

    def get_nodes_that_have_prerequisites(self) -> List['NodeLearningUnitYear']:
        return list(
            sorted(
                (
                    node_obj for node_obj in self.get_all_learning_unit_nodes()
                    if self.has_prerequisites(node_obj)
                ),
                key=lambda node_obj: node_obj.code
            )
        )

    def get_nodes_that_are_prerequisites(self) -> List['NodeLearningUnitYear']:  # TODO :: unit test
        return list(
            sorted(
                (
                    node_obj for node_obj in self.get_all_nodes()
                    if node_obj.is_learning_unit() and self.is_prerequisite(node_obj)
                ),
                key=lambda node_obj: node_obj.code
            )
        )

    def count_usages_distinct(self, node: 'Node') -> int:
        """Count the usage of the nodes with distinct parent. 2 links with the same parent are considered as 1 usage."""
        return len(set(self.search_links_using_node(node)))

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

    def _links_mapped_by_child_and_parent(self) -> Dict:
        return {
                str(link.child.entity_id) + str(link.parent.entity_id): link
                for link in self.get_all_links()
        }

    def get_link(self, parent: 'Node', child: 'Node') -> 'Link':
        my_map = self._links_mapped_by_child_and_parent()
        return my_map.get(str(child.entity_id) + str(parent.entity_id))

    def get_link_from_identity(self, link_id: 'LinkIdentity') -> Optional['Link']:
        return next(
            filter(lambda link: link.entity_id == link_id, self.get_all_links()),
            None
        )

    def prune(self, ignore_children_from: Set[EducationGroupTypesEnum] = None) -> 'ProgramTree':
        copied_root_node = copy.deepcopy(self.root_node)
        if ignore_children_from:
            copied_root_node.prune(ignore_children_from)
        return ProgramTree(
            root_node=copied_root_node,
            authorized_relationships=self.authorized_relationships,
            prerequisites=self.prerequisites,
            report=self.report
        )

    def get_ordered_mandatory_children_types(self, parent_node: 'Node') -> List[EducationGroupTypesEnum]:
        return self.authorized_relationships.get_ordered_mandatory_children_types(parent_node.node_type)

    def paste_node(
            self,
            node_to_paste: 'Node',
            paste_command: command.PasteElementCommand,
            tree_repository: 'ProgramTreeRepository',
            tree_version_repository: 'ProgramTreeVersionRepository'
    ) -> 'Link':
        """
        Add a node to the tree
        :param node_to_paste: Node to paste into the tree
        :param paste_command: a paste node command
        :param tree_repository: a tree repository
        :return: the created link
        """
        path_to_paste_to = paste_command.path_where_to_paste
        node_to_paste_to = self.get_node(path_to_paste_to)
        is_mandatory = paste_command.is_mandatory
        if node_to_paste_to.is_minor_major_option_list_choice():
            is_mandatory = False

        if node_to_paste_to.is_minor_major_list_choice() and node_to_paste.is_minor_major_deepening():
            link_type = LinkTypes.REFERENCE
        else:
            link_type = LinkTypes[paste_command.link_type] if paste_command.link_type else None

        validator = validators_by_business_action.PasteNodeValidatorList(
            self,
            node_to_paste,
            paste_command,
            link_type,
            tree_repository,
            tree_version_repository
        )
        validator.validate()

        return node_to_paste_to.add_child(
            node_to_paste,
            access_condition=paste_command.access_condition,
            is_mandatory=is_mandatory,
            block=paste_command.block,
            link_type=link_type,
            comment=paste_command.comment,
            comment_english=paste_command.comment_english,
            relative_credits=paste_command.relative_credits
        )

    def set_prerequisite(
            self,
            prerequisite_expression: 'PrerequisiteExpression',
            node_having_prerequisites: 'NodeLearningUnitYear'
    ) -> List['BusinessValidationMessage']:
        return self.prerequisites.set_prerequisite(node_having_prerequisites, prerequisite_expression, self)

    def get_remaining_children_after_detach(self, path_node_to_detach: 'Path'):
        children_with_counter = self.root_node.get_all_children_with_counter()
        children_with_counter.update([self.root_node])

        node_to_detach = self.get_node(path_node_to_detach)
        nodes_detached = node_to_detach.get_all_children_with_counter()
        nodes_detached.update([node_to_detach])
        children_with_counter.subtract(nodes_detached)

        return {node_obj for node_obj, number in children_with_counter.items() if number > 0}

    def detach_node(
            self,
            path_to_node_to_detach: Path,
            tree_repository: 'ProgramTreeRepository',
            prerequisite_repository: 'TreePrerequisitesRepository'
    ) -> 'Link':
        """
        Detach a node from tree
        :param path_to_node_to_detach: The path node to detach
        :param tree_repository: a tree repository
        :return: the suppressed link<
        """
        PathValidator(path_to_node_to_detach).validate()

        node_to_detach = self.get_node(path_to_node_to_detach)
        parent_path, *__ = path_to_node_to_detach.rsplit(PATH_SEPARATOR, 1)
        parent = self.get_node(parent_path)
        validators_by_business_action.DetachNodeValidatorList(
            self,
            node_to_detach,
            parent_path,
            tree_repository,
            prerequisite_repository
        ).validate()

        return parent.detach_child(node_to_detach)

    def __copy__(self) -> 'ProgramTree':
        return self.__deepcopy__(memodict={})

    def __deepcopy__(self, memodict: Dict = None) -> 'ProgramTree':
        if memodict is None:
            memodict = {}

        return ProgramTree(
            root_node=self.root_node.__deepcopy__(memodict),
            authorized_relationships=copy.copy(self.authorized_relationships),
            prerequisites=copy.deepcopy(self.prerequisites)
        )

    def get_relative_credits_values(self, child_node: 'NodeIdentity'):
        distinct_credits_repr = []
        node = self.get_node_by_code_and_year(child_node.code, child_node.year)

        for link_obj in self.search_links_using_node(node):
            if link_obj.relative_credits_repr not in distinct_credits_repr:
                distinct_credits_repr.append(link_obj.relative_credits_repr)
        return " ; ".join(
            set(["{}".format(credits) for credits in distinct_credits_repr])
        )

    def get_blocks_values(self, child_node: 'NodeIdentity'):
        node = self.get_node_by_code_and_year(child_node.code, child_node.year)
        return " ; ".join(
            [str(grp.block) for grp in self.search_links_using_node(node) if grp.block]
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

    def update_link(self, cmd: 'UpdateLinkCommand') -> 'Link':
        """
        Update link's attributes between parent_path and child_node
        :return: Updated link
        """
        parent_node = self.get_node_by_code_and_year(cmd.parent_node_code, cmd.parent_node_year)
        child_id = NodeIdentity(code=cmd.child_node_code, year=cmd.child_node_year)
        child_node = parent_node.get_direct_child_as_node(child_id)

        link_updated = parent_node.update_link_of_direct_child_node(
            child_id,
            relative_credits=cmd.relative_credits,
            access_condition=cmd.access_condition,
            is_mandatory=cmd.is_mandatory,
            block=cmd.block,
            link_type=cmd.link_type,
            comment=cmd.comment,
            comment_english=cmd.comment_english
        )

        validators_by_business_action.UpdateLinkValidatorList(
            self,
            child_node,
            link_updated
        ).validate()
        return link_updated

    @cached_result
    def _paths_by_node(self) -> Dict['Node', List['Path']]:
        paths_by_node = collections.defaultdict(list)
        for path, child_node in self.root_node.descendents:
            paths_by_node[child_node].append(path)
        return paths_by_node

    def search_paths_using_node(self, node: 'Node') -> List['Path']:
        return self._paths_by_node().get(node) or []

    def search_indirect_parents(self, node: 'Node') -> List['NodeGroupYear']:
        paths = self.search_paths_using_node(node)
        indirect_parents = []
        for path in paths:
            for parent in self.get_parents(path):
                if parent.is_indirect_parent() and node != parent:
                    indirect_parents.append(parent)
                    break
        return indirect_parents

    def contains(self, node: Node) -> bool:
        return node in self.get_all_nodes()

    def contains_identity(self, node_identity: 'NodeIdentity') -> bool:
        return any(node for node in self.get_all_nodes() if node.entity_id == node_identity)

    def get_all_prerequisites(self) -> List['Prerequisite']:
        return self.prerequisites.prerequisites

    def has_prerequisites(self, node: 'NodeLearningUnitYear') -> bool:
        return self.prerequisites.has_prerequisites(node)

    def is_prerequisite(self, node: 'NodeLearningUnitYear') -> bool:
        return self.prerequisites.is_prerequisite(node)

    def search_is_prerequisite_of(self, search_from_node: 'NodeLearningUnitYear') -> List['NodeLearningUnitYear']:
        return [
            self.get_node_by_code_and_year(node_identity.code, node_identity.year)
            for node_identity in self.prerequisites.search_is_prerequisite_of(search_from_node)
        ]

    def get_prerequisite(self, node: 'NodeLearningUnitYear') -> 'Prerequisite':
        return self.prerequisites.get_prerequisite(node)


def is_empty(parent_node: 'Node', relationships: 'AuthorizedRelationshipList'):
    for child_node in parent_node.children_as_nodes:
        if not is_empty(child_node, relationships):
            return False
        is_mandatory_children = child_node.node_type in relationships.get_ordered_mandatory_children_types(
            parent_node.node_type
        )
        if not is_mandatory_children:
            return False
    return True


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


def _path_contains(path: 'Path', node: 'Node') -> bool:
    return PATH_SEPARATOR + str(node.pk) in path

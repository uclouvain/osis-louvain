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
from _decimal import Decimal
from collections import OrderedDict
from typing import List, Set, Dict

import attr

from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType, MiniTrainingType, GroupType
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from base.models.enums.link_type import LinkTypes
from base.models.enums.proposal_type import ProposalType
from base.models.enums.quadrimesters import DerogationQuadrimester
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.models.enums.constraint_type import ConstraintTypes
from osis_common.ddd import interface
from program_management.ddd.business_types import *
from program_management.ddd.domain._campus import Campus
from program_management.ddd.domain.academic_year import AcademicYear
from program_management.ddd.domain.link import factory as link_factory
from program_management.ddd.domain.prerequisite import Prerequisite, NullPrerequisite
from program_management.models.enums.node_type import NodeType


class NodeFactory:

    @classmethod
    def copy_to_next_year(cls, copy_from_node: 'Node') -> 'Node':
        next_year = copy_from_node.entity_id.year + 1
        node_next_year = attr.evolve(
            copy_from_node,
            entity_id=NodeIdentity(copy_from_node.entity_id.code, next_year),
            year=next_year,
            children=[],
        )
        node_next_year._has_changed = True
        return node_next_year

    def get_node(self, type: NodeType, **node_attrs):
        node_cls = {
            NodeType.EDUCATION_GROUP: NodeEducationGroupYear,   # TODO: Remove when migration is done

            NodeType.GROUP: NodeGroupYear,
            NodeType.LEARNING_UNIT: NodeLearningUnitYear,
            NodeType.LEARNING_CLASS: NodeLearningClassYear
        }[type]
        if node_attrs.get('teaching_campus_name'):
            node_attrs['teaching_campus'] = Campus(
                name=node_attrs.pop('teaching_campus_name'),
                university_name=node_attrs.pop('teaching_campus_university_name'),
            )
        return node_cls(**node_attrs)


factory = NodeFactory()


@attr.s(frozen=True, slots=True)
class NodeIdentity(interface.EntityIdentity):
    code = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(slots=True, eq=False, hash=False)
class Node(interface.Entity):

    type = None

    node_id = attr.ib(type=int, default=None)
    node_type = attr.ib(type=EducationGroupTypesEnum, default=None)
    end_date = attr.ib(type=int, default=None)
    children = attr.ib(type=List['Link'], factory=list)
    code = attr.ib(type=str, default=None)
    title = attr.ib(type=str, default=None)
    year = attr.ib(type=int, default=None)
    credits = attr.ib(type=Decimal, default=None)

    entity_id = attr.ib(type=NodeIdentity)

    _children = children
    _deleted_children = attr.ib(type=List, factory=list)

    _academic_year = None
    _has_changed = False

    @entity_id.default
    def _entity_id(self) -> NodeIdentity:
        return NodeIdentity(self.code, self.year)

    def __str__(self):
        return '%(code)s (%(year)s)' % {'code': self.code, 'year': self.year}

    @property
    def pk(self):
        return self.node_id

    @property
    def academic_year(self):
        if self._academic_year is None:
            self._academic_year = AcademicYear(self.year)
        return self._academic_year

    @property
    def children(self) -> List['Link']:
        self._children.sort(key=lambda link_obj: link_obj.order or 0)
        return self._children

    @children.setter
    def children(self, new_children: List['Link']):
        self._children = new_children

    def is_learning_unit(self):
        return self.type == NodeType.LEARNING_UNIT

    def is_group_or_mini_or_training(self):
        return self.type == NodeType.GROUP or self.type == NodeType.EDUCATION_GROUP

    def is_finality(self) -> bool:
        return self.node_type in set(TrainingType.finality_types_enum())

    def is_master_2m(self) -> bool:
        return self.node_type in set(TrainingType.root_master_2m_types_enum())

    def is_option(self) -> bool:
        return self.node_type == MiniTrainingType.OPTION

    def is_training(self) -> bool:
        return self.node_type in TrainingType.all()

    def is_mini_training(self) -> bool:
        return self.node_type in MiniTrainingType.all()

    def is_group(self) -> bool:
        return self.node_type in GroupType.all()

    def is_minor_major_list_choice(self) -> bool:
        return self.node_type in GroupType.minor_major_list_choice_enums()

    def is_minor_or_deepening(self) -> bool:
        return self.node_type in MiniTrainingType.minors_and_deepening()

    def get_direct_child_as_node(self, node_id: 'NodeIdentity') -> 'Node':
        return next(node for node in self.get_direct_children_as_nodes() if node.entity_id == node_id)

    def get_all_children(
            self,
            ignore_children_from: Set[EducationGroupTypesEnum] = None,
    ) -> Set['Link']:
        children = set()
        for link in self.children:
            children.add(link)
            if ignore_children_from and link.child.node_type in ignore_children_from:
                continue
            children |= link.child.get_all_children(ignore_children_from=ignore_children_from)
        return children

    def get_option_list(self) -> Set['Node']:
        return {l.child for l in self.get_all_children() if l.child.is_option()}

    def get_finality_list(self) -> Set['Node']:
        return {l.child for l in self.get_all_children() if l.child.is_finality()}

    def get_all_children_as_nodes(
            self,
            take_only: Set[EducationGroupTypesEnum] = None,
            ignore_children_from: Set[EducationGroupTypesEnum] = None
    ) -> Set['Node']:
        """

        :param take_only: Result will only contain all children nodes if their type matches with this param
        :param ignore_children_from: Result will not contain all nodes and their children
        if their type matches with this param
        :return: A flat set of all children nodes
        """
        children_links = self.get_all_children(ignore_children_from=ignore_children_from)
        if take_only:
            return set(link.child for link in children_links if link.child.node_type in take_only)
        return set(link.child for link in children_links)

    def get_all_children_as_learning_unit_nodes(self) -> List['NodeLearningUnitYear']:
        sorted_links = sorted(
            [link for link in self.get_all_children() if isinstance(link.child, NodeLearningUnitYear)],
            key=lambda link: (link.order, link.parent.code)
        )
        return [link.child for link in sorted_links]

    @property
    def children_as_nodes(self) -> List['Node']:
        return [link.child for link in self.children]

    def get_direct_children_as_nodes(
            self,
            take_only: Set[EducationGroupTypesEnum] = None,
            ignore_children_from: Set[EducationGroupTypesEnum] = None
    ) -> List['Node']:
        """
            :param take_only: Result will only contain all children nodes if their type matches with this param
            :param ignore_children_from: Result will not contain direct nodes if their type matches with this param
            :return: A flat list of all direct children nodes
        """
        children = self.children_as_nodes
        if ignore_children_from:
            children = [child for child in children if child.node_type not in ignore_children_from]
        if take_only:
            children = [child for child in children if child.node_type in take_only]
        return children

    def children_and_reference_children(
            self,
            except_within: Set[EducationGroupTypesEnum] = None
    ) -> List['Link']:
        def is_link_to_keep(link: 'Link'):
            within_exception = except_within and link.parent.node_type in except_within
            return link.link_type != LinkTypes.REFERENCE or within_exception

        links = []
        for link in self.children:
            if is_link_to_keep(link):
                links.append(link)
            else:
                links += link.child.children
        return links

    def get_children_and_only_reference_children_except_within_minor_list(self) -> List['Link']:
        return self.children_and_reference_children(except_within={GroupType.MINOR_LIST_CHOICE})

    def get_children_types(self, include_nodes_used_as_reference=False) -> List[EducationGroupTypesEnum]:
        if not include_nodes_used_as_reference:
            return [link.child.node_type for link in self.children]

        list_child_nodes_types = []
        for link in self.children:
            if link.link_type == LinkTypes.REFERENCE:
                list_child_nodes_types += link.child.get_children_types(
                    include_nodes_used_as_reference=include_nodes_used_as_reference
                )
            else:
                list_child_nodes_types.append(link.child.node_type)
        return list_child_nodes_types

    @property
    def descendents(self) -> Dict['Path', 'Node']:   # TODO :: add unit tests
        return _get_descendents(self)

    def update_link_of_direct_child_node(
            self,
            child_id: 'NodeIdentity',
            relative_credits: int,
            access_condition: bool,
            is_mandatory: bool,
            block: int,
            link_type: str,
            comment: str,
            comment_english: str
    ) -> 'Link':
        link_to_update = next(link for link in self.children if link.child.entity_id == child_id)

        if self.is_minor_major_list_choice() and \
                not link_to_update.child.is_minor_major_list_choice():
            link_type = LinkTypes.REFERENCE

        link_to_update.relative_credits = relative_credits
        link_to_update.access_condition = access_condition
        link_to_update.is_mandatory = is_mandatory
        link_to_update.block = block
        link_to_update.link_type = link_type
        link_to_update.comment = comment
        link_to_update.comment_english = comment_english

        link_to_update._has_changed = True
        return link_to_update

    def add_child(self, node: 'Node', **link_attrs) -> 'Link':
        child = link_factory.get_link(parent=self, child=node, order=len(self.children), **link_attrs)
        self._children.append(child)
        child._has_changed = True
        return child

    def detach_child(self, node_to_detach: 'Node') -> 'Link':
        link_to_detach = next(link for link in self.children if link.child == node_to_detach)
        self._deleted_children.append(link_to_detach)
        self.children.remove(link_to_detach)
        return link_to_detach

    def get_link(self, link_id: int) -> 'Link':
        return next((link for link in self.children if link.pk == link_id), None)

    def up_child(self, node_to_up: 'Node') -> None:
        index = self.children_as_nodes.index(node_to_up)

        is_first_element = index == 0
        if is_first_element:
            return

        self.children[index].order_up()
        self.children[index-1].order_down()

    def down_child(self, node_to_down: 'Node') -> None:
        index = self.children_as_nodes.index(node_to_down)

        is_last_element = index == len(self.children) - 1
        if is_last_element:
            return

        self.children[index].order_down()
        self.children[index+1].order_up()


def _get_descendents(root_node: Node, current_path: 'Path' = None) -> Dict['Path', 'Node']:
    _descendents = OrderedDict()
    if current_path is None:
        current_path = str(root_node.pk)

    for link in root_node.children:
        child_path = "|".join([current_path, str(link.child.pk)])
        _descendents.update({
            **{child_path: link.child},
            **_get_descendents(link.child, current_path=child_path)
        })
    return _descendents


# TODO: Remove this class because unused when migration is done.
@attr.s(slots=True, hash=False)
class NodeEducationGroupYear(Node):

    type = NodeType.EDUCATION_GROUP

    constraint_type = attr.ib(type=ConstraintTypes, default=None)
    min_constraint = attr.ib(type=int, default=None)
    max_constraint = attr.ib(type=int, default=None)
    remark_fr = attr.ib(type=str, default=None)
    remark_en = attr.ib(type=str, default=None)
    offer_title_fr = attr.ib(type=str, default=None)
    offer_title_en = attr.ib(type=str, default=None)
    offer_partial_title_fr = attr.ib(type=str, default=None)
    offer_partial_title_en = attr.ib(type=str, default=None)
    category = attr.ib(type=Categories, default=None)


@attr.s(slots=True, eq=False, hash=False)
class NodeGroupYear(Node):

    type = NodeType.GROUP

    constraint_type = attr.ib(type=ConstraintTypes, default=None)
    min_constraint = attr.ib(type=int, default=None)
    max_constraint = attr.ib(type=int, default=None)
    remark_fr = attr.ib(type=str, default=None)
    remark_en = attr.ib(type=str, default=None)
    start_year = attr.ib(type=int, default=None)
    end_year = attr.ib(type=int, default=None)
    offer_title_fr = attr.ib(type=str, default=None)
    offer_title_en = attr.ib(type=str, default=None)
    group_title_fr = attr.ib(type=str, default=None)
    group_title_en = attr.ib(type=str, default=None)
    offer_partial_title_fr = attr.ib(type=str, default=None)
    offer_partial_title_en = attr.ib(type=str, default=None)
    category = attr.ib(type=GroupType, default=None)
    management_entity_acronym = attr.ib(type=str, default=None)
    teaching_campus = attr.ib(type=Campus, default=None)
    schedule_type = attr.ib(type=ScheduleTypeEnum, default=None)
    offer_status = attr.ib(type=ActiveStatusEnum, default=None)
    keywords = attr.ib(type=str, default=None)


@attr.s(slots=True, hash=False, eq=False)
class NodeLearningUnitYear(Node):

    type = NodeType.LEARNING_UNIT
    node_type = NodeType.LEARNING_UNIT

    is_prerequisite_of = attr.ib(type=List, factory=list)
    status = attr.ib(type=bool, default=None)
    periodicity = attr.ib(type=PeriodicityEnum, default=None)
    prerequisite = attr.ib(type=Prerequisite, default=NullPrerequisite())
    common_title_fr = attr.ib(type=str, default=None)
    specific_title_fr = attr.ib(type=str, default=None)
    common_title_en = attr.ib(type=str, default=None)
    specific_title_en = attr.ib(type=str, default=None)
    proposal_type = attr.ib(type=ProposalType, default=None)
    learning_unit_type = attr.ib(type=LearningContainerYearType, default=None)
    other_remark = attr.ib(type=str, default=None)
    quadrimester = attr.ib(type=DerogationQuadrimester, default=None)
    volume_total_lecturing = attr.ib(type=Decimal, default=None)
    volume_total_practical = attr.ib(type=Decimal, default=None)

    @property
    def full_title_fr(self) -> str:
        return "{}{}".format(
            self.common_title_fr,
            " - {}".format(self.specific_title_fr) if self.specific_title_fr else ''
        )

    @property
    def full_title_en(self) -> str:
        return "{}{}".format(
            self.common_title_en,
            " - {}".format(self.specific_title_en) if self.specific_title_en else ''
        )

    @property
    def has_prerequisite(self) -> bool:
        return bool(self.prerequisite)

    @property
    def is_prerequisite(self) -> bool:
        return bool(self.is_prerequisite_of)

    @property
    def has_proposal(self) -> bool:
        return bool(self.proposal_type)

    def get_is_prerequisite_of(self) -> List['NodeLearningUnitYear']:
        return sorted(self.is_prerequisite_of, key=lambda node: node.code)

    def set_prerequisite(self, prerequisite: Prerequisite):
        self.prerequisite = prerequisite
        self.prerequisite.has_changed = True

    def remove_all_prerequisite_items(self) -> None:
        self.prerequisite.remove_all_prerequisite_items()


class NodeLearningClassYear(Node):

    type = NodeType.LEARNING_CLASS

    def __init__(self, node_id: int, year: int, children: List['Link'] = None):
        super().__init__(node_id, children)
        self.year = year


class NodeNotFoundException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("The node cannot be found on the current tree")

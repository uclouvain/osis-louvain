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
from _decimal import Decimal
from typing import List, Set, Optional, Iterator, Tuple, Generator, Dict

import attr

from backoffice.settings.base import LANGUAGE_CODE_EN
from base.ddd.utils.converters import to_upper_case_converter
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType, MiniTrainingType, GroupType
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from base.models.enums.link_type import LinkTypes
from base.models.enums.proposal_type import ProposalType
from base.models.enums.quadrimesters import DerogationQuadrimester
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.models.enums.constraint_type import ConstraintTypes
from education_group.templatetags.academic_year_display import display_as_academic_year
from osis_common.ddd import interface
from program_management.ddd.business_types import *
from program_management.ddd.command import DO_NOT_OVERRIDE
from program_management.ddd.domain._campus import Campus
from program_management.ddd.domain.academic_year import AcademicYear
from program_management.ddd.domain.link import factory as link_factory
from program_management.ddd.domain.service.generate_node_abbreviated_title import GenerateNodeAbbreviatedTitle
from program_management.ddd.domain.service.generate_node_code import GenerateNodeCode
from program_management.ddd.domain.service.validation_rule import FieldValidationRule
from program_management.models.enums.node_type import NodeType


class NodeFactory:

    @classmethod
    def copy_to_next_year(cls, copy_from_node: 'Node') -> 'Node':
        next_year = copy_from_node.entity_id.year + 1
        end_year = cls._get_next_end_year(copy_from_node)
        node_next_year = attr.evolve(
            copy_from_node,
            entity_id=NodeIdentity(copy_from_node.entity_id.code, next_year),
            year=next_year,
            end_year=end_year,
            children=[],
            node_id=None,
        )
        node_next_year._has_changed = True
        return node_next_year

    @classmethod
    def _get_next_end_year(cls, copy_from_node: 'Node') -> Optional[int]:
        if not copy_from_node.end_year:
            return copy_from_node.end_year
        next_year = copy_from_node.entity_id.year + 1
        if copy_from_node.end_year < next_year:
            return next_year
        return copy_from_node.end_year

    def get_node(self, type: NodeType, **node_attrs) -> 'Node':
        node_cls = {
            NodeType.GROUP: NodeGroupYear,
            NodeType.LEARNING_UNIT: NodeLearningUnitYear,
            NodeType.LEARNING_CLASS: NodeLearningClassYear
        }[type]
        teaching_campus_name = node_attrs.pop('teaching_campus_name', None)
        teaching_campus_university_name = node_attrs.pop('teaching_campus_university_name', None)
        if teaching_campus_name:
            node_attrs['teaching_campus'] = Campus(
                name=teaching_campus_name,
                university_name=teaching_campus_university_name,
            )

        return node_cls(**node_attrs)

    def create_and_fill_from_node(
            self,
            create_from: 'Node',
            new_code: str,
            override_end_year_to: int = DO_NOT_OVERRIDE,
            override_start_year_to: int = DO_NOT_OVERRIDE
    ) -> 'Node':
        start_year = create_from.start_year if override_start_year_to == DO_NOT_OVERRIDE else override_start_year_to
        copied_node = attr.evolve(
            create_from,
            entity_id=NodeIdentity(code=new_code, year=create_from.entity_id.year),
            code=new_code,
            end_year=create_from.end_year if override_end_year_to == DO_NOT_OVERRIDE else override_end_year_to,
            # TODO: Replace end_date by end_year
            end_date=create_from.end_date if override_end_year_to == DO_NOT_OVERRIDE else override_end_year_to,
            start_year=start_year,
            children=[],
            node_id=None,
        )
        if copied_node.type == NodeType.GROUP:
            copied_node.constraint_type = None
            copied_node.min_constraint = None
            copied_node.max_constraint = None
            copied_node.remark_en = None
            copied_node.remark_fr = None
            if copied_node.node_type in GroupType:
                default_credit = FieldValidationRule.get_initial_value_or_none(create_from.node_type, 'credits')
                copied_node.credits = default_credit
        copied_node._has_changed = True
        return copied_node

    def generate_from_parent(self, parent_node: 'Node', child_type: 'EducationGroupTypesEnum') -> 'Node':
        generated_child_title = FieldValidationRule.get(
            child_type,
            'title_fr'
        ).initial_value
        default_credits = FieldValidationRule.get_initial_value_or_none(child_type, 'credits')
        default_title_en = FieldValidationRule.get_initial_value_or_none(child_type, 'title_en')
        child = self.get_node(
            type=NodeType.GROUP,
            node_type=child_type,
            code=GenerateNodeCode.generate_from_parent_node(parent_node, child_type, False),
            title=GenerateNodeAbbreviatedTitle.generate(
                parent_node=parent_node,
                child_node_type=child_type,
            ),
            year=parent_node.year,
            teaching_campus=parent_node.teaching_campus,
            management_entity_acronym=parent_node.management_entity_acronym,
            group_title_fr=generated_child_title,
            group_title_en=default_title_en,
            start_year=parent_node.year,
            credits=default_credits
        )
        child._has_changed = True
        return child


factory = NodeFactory()


@attr.s(frozen=True, slots=True)
class NodeIdentity(interface.EntityIdentity):
    code = attr.ib(type=str, converter=to_upper_case_converter)
    year = attr.ib(type=int)


@attr.s(slots=True, eq=False, hash=False)
class Node(interface.Entity):

    type = None

    node_id = attr.ib(type=int, default=None)
    node_type = attr.ib(type=EducationGroupTypesEnum, default=None)
    end_date = attr.ib(type=int, default=None)
    start_year = attr.ib(type=int, default=None)
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
        return '%(code)s (%(year)s)' % {'code': self.code, 'year': display_as_academic_year(self.year)}

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
        return self.type == NodeType.GROUP

    def is_finality(self) -> bool:
        return self.node_type in set(TrainingType.finality_types_enum())

    def is_finality_list_choice(self) -> bool:
        return self.node_type in {GroupType.FINALITY_120_LIST_CHOICE, GroupType.FINALITY_180_LIST_CHOICE}

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

    def is_minor_major_option_list_choice(self) -> bool:
        return self.node_type in GroupType.minor_major_option_list_choice_enums()

    def is_option_list_choice(self):
        return self.node_type == GroupType.OPTION_LIST_CHOICE

    def is_minor_or_deepening(self) -> bool:
        return self.is_minor() or self.is_deepening()

    def is_minor(self) -> bool:
        return self.node_type in MiniTrainingType.minors_enum()

    def is_minor_major_deepening(self) -> bool:
        return self.is_minor() or self.is_major() or self.is_deepening()

    def is_deepening(self) -> bool:
        return self.node_type == MiniTrainingType.DEEPENING

    def is_major(self) -> bool:
        return self.node_type == MiniTrainingType.FSA_SPECIALITY

    def is_common_core(self) -> bool:
        return self.node_type == GroupType.COMMON_CORE

    def is_bachelor(self) -> bool:
        return self.node_type == TrainingType.BACHELOR

    def is_indirect_parent(self) -> bool:
        return self.is_training() or self.is_minor_or_deepening()

    def get_direct_child_as_node(self, node_id: 'NodeIdentity') -> 'Node':
        return next(node for node in self.get_direct_children_as_nodes() if node.entity_id == node_id)

    def get_direct_child(self, node_id: 'NodeIdentity') -> 'Link':
        return next(link for link in self.children if link.child.entity_id == node_id)

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
        return {link.child for link in self.get_all_children() if link.child.is_option()}

    def get_finality_list(self) -> Set['Node']:
        return {link.child for link in self.get_all_children() if link.child.is_finality()}

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

    def get_all_children_with_counter(self) -> collections.Counter:
        nodes = (child for path, child in self.descendents)
        return collections.Counter(nodes)

    def get_all_children_as_learning_unit_nodes(self) -> List['NodeLearningUnitYear']:
        sorted_links = sorted(
            [link for link in self.get_all_children() if link.child.is_learning_unit()],
            key=lambda link: (link.order, link.parent.code)
        )
        return [link.child for link in sorted_links]

    @property
    def children_as_nodes(self) -> List['Node']:
        return [link.child for link in self.children]

    @property
    def children_as_nodes_with_respect_to_reference_link(self) -> List['Node']:
        children = []
        for link in self.children:
            if link.is_reference():
                children.extend(link.child.children_as_nodes_with_respect_to_reference_link)
            else:
                children.append(link.child)
        return children

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

    def get_training_children(self) -> Iterator['Node']:
        return (node for node in self.children_as_nodes if node.is_training())

    @property
    def descendents(self) -> Generator[Tuple['Path', 'Node'], None, None]:   # TODO :: add unit tests
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
            link_type = LinkTypes.REFERENCE.name

        link_to_update.relative_credits = relative_credits
        link_to_update.access_condition = access_condition
        link_to_update.is_mandatory = is_mandatory
        link_to_update.block = block
        link_to_update.link_type = LinkTypes[link_type] if link_type else None
        link_to_update.comment = comment
        link_to_update.comment_english = comment_english

        link_to_update._has_changed = True
        return link_to_update

    def add_child(self, node: 'Node', **link_attrs) -> 'Link':
        max_order = max((child.order for child in self.children), default=-1)
        child = link_factory.get_link(parent=self, child=node, order=max_order + 1, **link_attrs)
        self._children.append(child)
        child._has_changed = True
        return child

    def detach_child(self, node_to_detach: 'Node') -> 'Link':
        link_to_detach = self._move_down_link_to_detach(node_to_detach)
        self._deleted_children.append(link_to_detach)
        self.children.remove(link_to_detach)
        return link_to_detach

    def _move_down_link_to_detach(self, node_to_detach: 'Node') -> 'Link':
        link_to_detach = None
        for link in self.children:
            if link.child == node_to_detach:
                link_to_detach = link
            elif link_to_detach:
                link.parent.down_child(link_to_detach.child)
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

    def prune(self, ignore_children_from: Set[EducationGroupTypesEnum]) -> None:
        if self.node_type in ignore_children_from:
            self.children = []
        for child_link in self.children:
            child_link.child.prune(ignore_children_from=ignore_children_from)

    def __deepcopy__(self, memodict: Dict = None) -> 'Node':
        if memodict is None:
            memodict = {}

        if self.entity_id in memodict:
            return memodict[self.entity_id]

        copy_node = attr.evolve(self, children=[])
        memodict[copy_node.entity_id] = copy_node
        copy_node.children = [l.__deepcopy__(memodict) for l in self.children]

        return copy_node


def _get_descendents(root_node: Node, current_path: 'Path' = None) -> Generator[Tuple['Path', 'Node'], None, None]:
    if current_path is None:
        current_path = str(root_node.pk)

    for link in root_node.children:
        child_path = "|".join((current_path, str(link.child.pk)))
        yield child_path, link.child
        yield from _get_descendents(link.child, current_path=child_path)


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
    version_name = attr.ib(type=str, default=None)
    version_title_fr = attr.ib(type=str, default=None)
    version_title_en = attr.ib(type=str, default=None)
    transition_name = attr.ib(type=str, default=None)
    category = attr.ib(type=GroupType, default=None)
    management_entity_acronym = attr.ib(type=str, default=None)
    teaching_campus = attr.ib(type=Campus, default=None)
    schedule_type = attr.ib(type=ScheduleTypeEnum, default=None)
    offer_status = attr.ib(type=ActiveStatusEnum, default=None)
    keywords = attr.ib(type=str, default=None)

    def __str__(self):
        if self.version_name:
            return "{}[{}{}] - {} ({})".format(self.title,
                                               self.version_name,
                                               self.get_formatted_transition_name(),
                                               self.code,
                                               self.academic_year)
        return "{}{} - {} ({})".format(self.title, self.get_formatted_transition_name(), self.code, self.academic_year)

    def full_acronym(self) -> str:
        if self.version_name:
            return "{}[{}{}]".format(self.title, self.version_name, self.get_formatted_transition_name())
        return '{}{}'.format(self.title, self.get_formatted_transition_name())

    def full_title(self) -> str:
        title = self.offer_title_fr
        if self.is_group():
            title = self.group_title_fr
        elif self.is_finality():
            title = self.offer_partial_title_fr
        if self.version_title_fr:
            return "{}[{}]".format(title, self.version_title_fr)
        return title

    def get_formatted_transition_name(self):
        if self.transition_name:
            return '-{}'.format(self.transition_name) if self.version_name else '[{}]'.format(self.transition_name)
        return ''


@attr.s(slots=True, hash=False, eq=False)
class NodeLearningUnitYear(Node):

    type = NodeType.LEARNING_UNIT
    node_type = attr.ib(type=NodeType, default=NodeType.LEARNING_UNIT)

    status = attr.ib(type=bool, default=None)
    periodicity = attr.ib(type=PeriodicityEnum, default=None)
    common_title_fr = attr.ib(type=str, default=None)
    specific_title_fr = attr.ib(type=str, default=None)
    common_title_en = attr.ib(type=str, default=None)
    specific_title_en = attr.ib(type=str, default=None)
    proposal_type = attr.ib(type=ProposalType, default=None)
    learning_unit_type = attr.ib(type=LearningContainerYearType, default=None)
    other_remark = attr.ib(type=str, default=None)
    other_remark_english = attr.ib(type=str, default=None)
    quadrimester = attr.ib(type=DerogationQuadrimester, default=None)
    volume_total_lecturing = attr.ib(type=Decimal, default=None)
    volume_total_practical = attr.ib(type=Decimal, default=None)

    def equals(self, learning_unit_year) -> bool:
        return learning_unit_year.entity_id.code == self.entity_id.code \
               and learning_unit_year.entity_id.year == self.entity_id.year

    @property
    def full_title_fr(self) -> str:
        return _get_full_title(self.common_title_fr, self.specific_title_fr)

    @property
    def full_title_en(self) -> str:
        return _get_full_title(self.common_title_en, self.specific_title_en)

    @property
    def has_proposal(self) -> bool:
        return bool(self.proposal_type)


def _get_full_title(common_title, specific_title):
    specific_title = "{}{}".format(" - " if common_title else '',
                                   specific_title) if specific_title else ''
    return "{}{}".format(
        common_title if common_title else '',
        specific_title
    )


class NodeLearningClassYear(Node):

    type = NodeType.LEARNING_CLASS

    def __init__(self, node_id: int, year: int, children: List['Link'] = None):
        super().__init__(node_id, children)
        self.year = year


class NodeNotFoundException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("The node cannot be found on the current tree")


def build_title(node: 'NodeGroupYear', language: str):
    if language == LANGUAGE_CODE_EN and node.offer_title_en:
        offer_title = " - {}".format(
            node.offer_title_en
        ) if node.offer_title_en else ''
    else:
        offer_title = " - {}".format(
            node.offer_title_fr
        ) if node.offer_title_fr else ''
    if language == LANGUAGE_CODE_EN and node.version_title_en:
        version_title = " [{}]".format(node.version_title_en)
    else:
        version_title = " [{}]".format(node.version_title_fr) if node.version_title_fr else ''
    return "{}{}".format(offer_title, version_title)

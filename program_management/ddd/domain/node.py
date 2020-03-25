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
from typing import List, Set, Dict

from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType
from base.models.enums.link_type import LinkTypes
from base.models.enums.proposal_type import ProposalType
from program_management.ddd.business_types import *
from program_management.ddd.domain.link import factory as link_factory
from program_management.ddd.domain.prerequisite import Prerequisite
from program_management.models.enums.node_type import NodeType


class NodeFactory:
    def get_node(self, type: NodeType, **node_attrs):
        node_cls = {
            NodeType.EDUCATION_GROUP: NodeEducationGroupYear,   # TODO: Remove when migration is done

            NodeType.GROUP: NodeGroupYear,
            NodeType.LEARNING_UNIT: NodeLearningUnitYear,
            NodeType.LEARNING_CLASS: NodeLearningClassYear
        }[type]
        return node_cls(**node_attrs)


factory = NodeFactory()


class Node:

    acronym = None
    year = None

    def __init__(
            self,
            node_id: int = None,
            node_type: EducationGroupTypesEnum = None,
            end_date: int = None,
            children: List['Link'] = None,
            acronym: str = None,
            title: str = None,
            year: int = None,
            proposal_type: ProposalType = None
    ):
        self.node_id = node_id
        if children is None:
            children = []
        self.children = children
        self.node_type = node_type
        self.end_date = end_date
        self.acronym = acronym
        self.title = title
        self.year = year
        self.proposal_type = proposal_type

    def __eq__(self, other):
        return self.node_id == other.node_id

    def __hash__(self):
        return hash(self.node_id)

    def __str__(self):
        return '%(acronym)s (%(year)s)' % {'acronym': self.acronym, 'year': self.year}

    def __repr__(self):
        return str(self)

    @property
    def pk(self):
        return self.node_id

    def is_finality(self) -> bool:
        return self.node_type in set(TrainingType.finality_types_enum())

    def is_master_2m(self) -> bool:
        return self.node_type in set(TrainingType.root_master_2m_types_enum())

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
        result = set()
        for link in self.children:
            child = link.child
            result.add(link.child)
            if ignore_children_from and child.node_type in ignore_children_from:
                continue
            result |= child.get_all_children_as_nodes()
        if take_only:
            return set(n for n in result if n.node_type in take_only)
        return result

    @property
    def children_as_nodes(self) -> List['Node']:
        return [link.child for link in self.children]

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

    def add_child(self, node: 'Node', **kwargs):
        child = link_factory.get_link(parent=self, child=node, **kwargs)
        self.children.append(child)

    def detach_child(self, node_id: int):
        self.children = [link for link in self.children if link.child.pk == node_id]


def _get_descendents(root_node: Node, current_path: 'Path' = None) -> Dict['Path', 'Node']:
    _descendents = {}
    if current_path is None:
        current_path = str(root_node.pk)

    for link in root_node.children:
        child_path = "|".join([current_path, str(link.child.pk)])
        _descendents.update({
            **{child_path: link.child},
            **_get_descendents(link.child, current_path=child_path)
        })
    return _descendents


class NodeEducationGroupYear(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class NodeGroupYear(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class NodeLearningUnitYear(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prerequisite = None  # FIXME : Should be of type Prerequisite?
        self.is_prerequisite_of = []

    @property
    def has_prerequisite(self) -> bool:
        return bool(self.prerequisite)

    @property
    def is_prerequisite(self) -> bool:
        return bool(self.is_prerequisite_of)

    @property
    def has_proposal(self) -> bool:
        return bool(self.proposal_type)

    def set_prerequisite(self, prerequisite: Prerequisite):
        self.prerequisite = prerequisite


class NodeLearningClassYear(Node):
    def __init__(self, node_id: int, year: int, children: List['Link'] = None):
        super().__init__(node_id, children)
        self.year = year


class NodeNotFoundException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("The node cannot be found on the current tree")

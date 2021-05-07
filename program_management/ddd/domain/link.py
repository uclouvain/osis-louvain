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
from typing import Dict, List

import attr

from base.models.enums.link_type import LinkTypes
from base.models.enums.quadrimesters import DerogationQuadrimester
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYearIdentity
from osis_common.ddd import interface
from program_management.ddd.business_types import *
from program_management.models.enums.node_type import NodeType


@attr.s(frozen=True, slots=True)
class LinkIdentity(interface.EntityIdentity):
    parent_code = attr.ib(type=str)
    child_code = attr.ib(type=str)
    parent_year = attr.ib(type=int)
    child_year = attr.ib(type=int)

    def __str__(self):
        return "{parent_code} ({verbose_parent_year}) - {child_code} ({verbose_child_year})".format(
            parent_code=self.parent_code,
            verbose_parent_year=AcademicYearIdentity.get_verbose_year(self.parent_year),
            child_code=self.child_code,
            verbose_child_year=AcademicYearIdentity.get_verbose_year(self.child_year),
        )

    def get_next_year_link_identity(self) -> 'LinkIdentity':
        return attr.evolve(self, parent_year=self.parent_year + 1, child_year=self.child_year + 1)


@attr.s(slots=True, str=False, hash=False, eq=False)
class Link(interface.Entity):

    parent = attr.ib(type='Node')  # type: Node
    child = attr.ib(type='Node')  # type: Node
    pk = attr.ib(type=int, default=None)
    relative_credits = attr.ib(type=int, default=None)
    min_credits = attr.ib(type=int, default=None)
    max_credits = attr.ib(type=int, default=None)
    is_mandatory = attr.ib(type=bool, default=True)
    block = attr.ib(type=str, default=None)
    access_condition = attr.ib(type=bool, default=False)
    comment = attr.ib(type=str, default=None)
    comment_english = attr.ib(type=str, default=None)
    own_comment = attr.ib(type=str, default=None)
    quadrimester_derogation = attr.ib(type=DerogationQuadrimester, default=None)
    link_type = attr.ib(type=LinkTypes, default=None)
    order = attr.ib(type=int, default=None)

    entity_id = attr.ib(type=LinkIdentity)

    _has_changed = False

    @entity_id.default
    def _link_identity(self) -> LinkIdentity:
        if self.parent and self.child:
            return LinkIdentity(self.parent.code, self.child.code, self.parent.year, self.child.year)

    @property
    def has_changed(self):
        return self._has_changed

    def __str__(self):
        return self.__format_node(self.parent) + " - " + self.__format_node(self.child)

    def __format_node(self, node: 'Node') -> str:
        node_str = "{node.code} ({node.academic_year})"
        if node.is_group_or_mini_or_training() and node.version_name:
            node_str = "{node.code}[{node.version_name}] ({node.academic_year})"
        return node_str.format(node=node)

    def __eq__(self, other):
        if isinstance(other, Link):
            return self.entity_id == other.entity_id
        return False

    def __hash__(self):
        return hash(self.entity_id)

    def __deepcopy__(self, memodict: Dict = None) -> 'Link':
        if memodict is None:
            memodict = {}

        copy_link = attr.evolve(
            self,
            parent=self.parent.__deepcopy__(memodict) if self.parent else None,
            child=self.child.__deepcopy__(memodict) if self.child else None
        )

        return copy_link

    def is_reference(self):
        return self.link_type == LinkTypes.REFERENCE

    @property
    def block_repr(self) -> FieldValueRepresentation:
        if self.block:
            block_in_array = [i for i in str(self.block)]
            return " ; ".join(
                block_in_array
            )
        return ''

    @property
    def block_max_value(self) -> int:
        return int(str(self.block)[-1]) if self.block else 0

    @property
    def relative_credits_repr(self) -> FieldValueRepresentation:
        return "{} / {:f}".format(self.relative_credits, self.child.credits.to_integral_value())

    def is_link_with_learning_unit(self):
        return self.child.is_learning_unit()

    def is_link_with_group(self):
        return self.child.is_group_or_mini_or_training()

    def order_up(self):
        self.order -= 1
        self._has_changed = True

    def order_down(self):
        self.order += 1
        self._has_changed = True

    def has_same_values_as(self, other_link: 'Link') -> bool:
        return not bool(self.get_conflicted_fields(other_link))

    def get_conflicted_fields(self, other_link: 'Link') -> List[str]:
        fields_not_to_compare = ("year", "entity_id", "child", "parent", "pk", "order")
        conflicted_fields = []
        for field_name in other_link.__slots__:
            if field_name in fields_not_to_compare:
                continue
            if getattr(self, field_name) != getattr(other_link, field_name):
                conflicted_fields.append(field_name)
        return conflicted_fields


@attr.s(slots=True, str=False, hash=False, eq=False)
class LinkWithChildLeaf(Link):
    relative_credits = attr.ib(type=int, default=attr.Factory(lambda self: self.child.credits, takes_self=True))


class LinkWithChildBranch(Link):
    def __init__(self, *args, **kwargs):
        super(LinkWithChildBranch, self).__init__(*args, **kwargs)


class LinkBuilder:
    def from_link(self, from_link: 'Link', parent: 'Node', child: 'Node'):
        new_link = attr.evolve(from_link, parent=parent, child=child)
        new_link._has_changed = True
        return new_link


class LinkFactory:

    def copy_to_next_year(self, copy_from_link: 'Link', parent_next_year: 'Node', child_next_year: 'Node') -> 'Link':
        link_next_year = attr.evolve(
            copy_from_link,
            parent=parent_next_year,
            child=child_next_year,
        )  # TODO :: to move into LinkBuilder
        link_next_year._has_changed = True
        return link_next_year

    def get_link(self, parent: 'Node', child: 'Node', **kwargs) -> Link:
        if parent and parent.node_type == NodeType.LEARNING_UNIT.name:
            return LinkWithChildLeaf(parent, child, **kwargs)
        else:
            return LinkWithChildBranch(parent, child, **kwargs)

    def create_link(self, *args, **kwargs) -> Link:
        link_created = self.get_link(*args, **kwargs)
        link_created._has_changed = True
        return link_created


factory = LinkFactory()

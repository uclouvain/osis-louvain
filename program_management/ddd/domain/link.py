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

import attr

from base.models.enums.link_type import LinkTypes
from base.models.enums.quadrimesters import DerogationQuadrimester
from osis_common.ddd import interface
from program_management.ddd.business_types import *
from program_management.models.enums.node_type import NodeType


@attr.s(frozen=True, slots=True)
class LinkIdentity(interface.EntityIdentity):
    parent_code = attr.ib(type=str)
    child_code = attr.ib(type=str)
    parent_year = attr.ib(type=int)
    child_year = attr.ib(type=int)


@attr.s(slots=True, str=False, hash=False, eq=False)
class Link(interface.Entity):

    parent = attr.ib(type='Node')
    child = attr.ib(type='Node')
    pk = attr.ib(type=int, default=None)
    relative_credits = attr.ib(type=int, default=None)
    min_credits = attr.ib(type=int, default=None)
    max_credits = attr.ib(type=int, default=None)
    is_mandatory = attr.ib(type=bool, default=False)
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
        return "%(parent)s - %(child)s" % {'parent': self.parent, 'child': self.child}

    def __eq__(self, other):
        if isinstance(other, Link):
            return self.entity_id == other.entity_id
        return False

    def __hash__(self):
        return hash(self.entity_id)

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


class LinkWithChildLeaf(Link):
    def __init__(self, *args, **kwargs):
        super(LinkWithChildLeaf, self).__init__(*args, **kwargs)


class LinkWithChildBranch(Link):
    def __init__(self, *args, **kwargs):
        super(LinkWithChildBranch, self).__init__(*args, **kwargs)


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


factory = LinkFactory()

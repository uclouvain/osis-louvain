##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import itertools
from collections import namedtuple
from typing import Dict, Optional, List

import attr

from base.models.entity_version import EntityVersion

EntityAttributes = namedtuple("EntityAttributes", "acronym entity_type entity_id")


@attr.s(frozen=True, slots=True)
class MainEntityStructure:
    @attr.s(slots=True)
    class Node:
        entity_id = attr.ib(type=int)
        parent_id = attr.ib(type=Optional[int])
        parents = attr.ib(type=List[int])
        acronym = attr.ib(type=str)
        entity_type = attr.ib(type=str)

        def is_faculty(self):
            return EntityVersion.is_faculty_cls(self.entity_type, self.acronym)

    nodes = attr.ib(type=Dict[int, 'MainEntityStructure.Node'])

    def get_direct_children(self, parent_entity_id: int) -> List['EntityAttributes']:
        nodes = (node for node in self.nodes.values() if node.parent_id == parent_entity_id)
        return [self.get_entity_attributes(node.entity_id) for node in nodes]

    def get_children(self, parent_entity_id: int) -> List['EntityAttributes']:
        children = self.get_direct_children(parent_entity_id)
        children += itertools.chain.from_iterable(self.get_children(child.entity_id) for child in children)
        return children

    def get_containing_faculty(self, entity_id: int) -> Optional['EntityAttributes']:
        return self.get_entity_faculty(entity_id) or self.get_entity_attributes(entity_id)

    def get_entity_attributes(self, entity_id: int) -> Optional['EntityAttributes']:
        try:
            node = self.nodes[entity_id]
            return EntityAttributes(acronym=node.acronym, entity_type=node.entity_type, entity_id=node.entity_id)
        except KeyError:
            return None

    def get_entity_faculty(self, entity_id: int) -> Optional['EntityAttributes']:
        try:
            node = self.nodes[entity_id]
        except KeyError:
            return None

        if node.is_faculty():
            return self.get_entity_attributes(entity_id)
        return self.get_entity_faculty(node.parent_id) if node.parent_id else None

    def in_same_faculty(self, entity_id: int, other_entity_id: int):
        return self.get_containing_faculty(entity_id) == self.get_containing_faculty(other_entity_id)


def load_main_entity_structure() -> MainEntityStructure:
    tree_rows = EntityVersion.objects.get_main_tree(with_expired=True)
    nodes = {
        row["entity_id"]: MainEntityStructure.Node(
            entity_id=row["entity_id"],
            parent_id=row["parent_id"],
            parents=row["parents"],
            acronym=row["acronym"],
            entity_type=row["entity_type"]
        )
        for row in tree_rows
    }
    return MainEntityStructure(nodes)

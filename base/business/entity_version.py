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
from datetime import datetime
from typing import Iterable, Dict, Optional, List

import attr

from base.models.entity_version import EntityVersion, find_latest_version


@attr.s(frozen=True, slots=True)
class MainEntityStructure:
    @attr.s(slots=True)
    class Node:
        entity_version = attr.ib(type=EntityVersion)
        parent = attr.ib(type=Optional['MainEntityStructure.Node'], default=None)
        direct_children = attr.ib(type=List['MainEntityStructure.Node'], factory=list)

        def faculty(self) -> Optional['MainEntityStructure.Node']:
            if self.entity_version.is_faculty():
                return self
            if self.parent:
                return self.parent.faculty()
            return None

        def containing_faculty(self):
            return self.faculty() or self

        def get_all_children(self) -> List['MainEntityStructure.Node']:
            return list(itertools.chain.from_iterable((child.get_all_children() for child in self.direct_children))) + \
                self.direct_children

    root = attr.ib(type='MainEntityStructure.Node')
    nodes = attr.ib(type=Dict[int, 'MainEntityStructure.Node'])

    def get_node(self, entity_id: int) -> Optional['MainEntityStructure.Node']:
        return self.nodes.get(entity_id)

    def in_same_faculty(self, entity_id: int, other_entity_id: int):
        node = self.nodes.get(entity_id)
        another_node = self.nodes.get(other_entity_id)
        return (node and node.containing_faculty()) == (another_node and another_node.containing_faculty())


def load_main_entity_structure(date: datetime.date) -> MainEntityStructure:
    all_current_entities_version = find_latest_version(date=date).of_main_organization  # type: Iterable[EntityVersion]

    nodes = {ev.entity.id: MainEntityStructure.Node(ev) for ev in all_current_entities_version}
    for ev in all_current_entities_version:
        if not ev.parent_id:
            continue
        nodes[ev.entity.id].parent = nodes[ev.parent_id]
        nodes[ev.parent_id].direct_children.append(nodes[ev.entity.id])

    root = next((value for key, value in nodes.items() if not value.parent))
    return MainEntityStructure(root, nodes)

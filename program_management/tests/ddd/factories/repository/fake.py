# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from typing import List, Type, Optional, Set

from osis_common.ddd import interface
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception, program_tree
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch
from testing.mocks import FakeRepository


def get_fake_node_repository(root_entities: List['Node']) -> Type['FakeRepository']:
    class_name = 'FakeNodeRepository'
    return type(class_name, (FakeRepository,), {
        "root_entities": root_entities.copy(),
        "not_found_exception_class": exception.NodeNotFoundException,
        "search": _search_nodes,
    })


def get_fake_program_tree_repository(root_entities: List['ProgramTree']) -> Type['FakeRepository']:
    class_name = "FakeProgramTreeRepository"
    return type(class_name, (FakeRepository,), {
        "create": _create_program_tree,
        "search": _search_program_trees,
        "root_entities": root_entities.copy(),
        "not_found_exception_class": exception.ProgramTreeNotFoundException,
        "delete": _delete_program_tree,
        "search_from_children": _search_from_children,
        "get_all_identities": _get_all_identities,
    })


def get_fake_program_tree_version_repository(root_entities: List['ProgramTreeVersion']) -> Type['FakeRepository']:
    class_name = "FakeProgramTreeVersionRepository"
    return type(class_name, (FakeRepository,), {
        "create": _create_program_tree_version,
        "root_entities": root_entities.copy(),
        "not_found_exception_class": exception.ProgramTreeVersionNotFoundException,
        "delete": _delete_program_tree_version,
        "search": _search_program_tree_version,
        "search_versions_from_trees": _search_versions_from_trees,
    })


@classmethod
def _create_program_tree(cls, program_tree: 'ProgramTree', **_) -> interface.EntityIdentity:
    cls.root_entities.append(program_tree)
    return program_tree.entity_id


@classmethod
def _create_program_tree_version(cls, program_tree_version: 'ProgramTreeVersion', **_) -> interface.EntityIdentity:
    cls.root_entities.append(program_tree_version)
    return program_tree_version.entity_id


@classmethod
def _delete_program_tree_version(
        cls,
        entity_id: 'ProgramTreeVersionIdentity',
        delete_program_tree_service: interface.ApplicationService) -> None:
    tree_version = cls.get(entity_id)

    idx = -1
    for idx, entity in enumerate(cls.root_entities):
        if entity.entity_id == entity_id:
            break
    if idx >= 0:
        cls.root_entities.pop(idx)

    cmd = command.DeleteProgramTreeCommand(code=tree_version.tree.root_node.code, year=tree_version.tree.root_node.year)
    delete_program_tree_service(cmd)


@classmethod
def _delete_program_tree(
        cls,
        entity_id: 'ProgramTreeIdentity',
        delete_node_service: interface.ApplicationService) -> None:
    program_tree = cls.get(entity_id)
    nodes = program_tree.get_all_nodes()

    idx = -1
    for idx, entity in enumerate(cls.root_entities):
        if entity.entity_id == entity_id:
            break
    if idx >= 0:
        cls.root_entities.pop(idx)

    for node in nodes:
        cmd = command.DeleteNodeCommand(code=node.code, year=node.year, node_type=node.node_type.name,
                                        acronym=node.title)
        delete_node_service(cmd)


@classmethod
def _search_program_trees(
        cls,
        entity_ids: List['ProgramTreeIdentity'] = None,
        code: str = None,
        **kwargs
) -> List['ProgramTree']:
    result = []
    if entity_ids:
        return [root_entity for root_entity in cls.root_entities if root_entity.entity_id in entity_ids]
    if code:
        return [root_entity for root_entity in cls.root_entities if code in root_entity.entity_id.code]
    return result


@classmethod
def _search_program_tree_version(
        cls,
        entity_ids: Optional[List['ProgramTreeVersionIdentity']] = None,
        version_name: str = None,
        offer_acronym: str = None,
        transition_name: str = None,
        year: int = None,
        **kwargs
) -> List['ProgramTreeVersion']:
    result = cls.root_entities  # type: List[ProgramTreeVersion]
    if version_name is not None:
        result = (tree_version for tree_version in result if tree_version.version_name == version_name)
    if offer_acronym is not None:
        result = (tree_version for tree_version in result if tree_version.entity_id.offer_acronym == offer_acronym)
    if transition_name is not None:
        result = (tree_version for tree_version in result if tree_version.transition_name == transition_name)
    if year:
        result = (tree_version for tree_version in result if tree_version.entity_id.year == year)
    return list(result)


@classmethod
def _search_from_children(cls, node_ids: List['NodeIdentity'], **kwargs) -> List['ProgramTree']:
    result = []
    set_node_ids = set(node_ids)
    for tree in cls.root_entities:
        children_nodes = tree.get_all_nodes() - {tree.root_node}
        children_nodes_ids = set([node.entity_id for node in children_nodes])
        if not children_nodes_ids.isdisjoint(set_node_ids):
            result.append(tree)
    return result


@classmethod
def _search_versions_from_trees(cls, trees: List['ProgramTree']) -> List['ProgramTreeVersion']:
    tree_entities = {tree.entity_id for tree in trees}
    return [tree_version for tree_version in cls.root_entities if tree_version.tree.entity_id in tree_entities]


@classmethod
def _search_nodes(cls, node_ids: List['NodeIdentity'] = None, year: int = None, **kwargs) -> List['Node']:
    if node_ids:
        return [node for node in cls.root_entities if node.entity_id in node_ids]
    if year:
        return [node for node in cls.root_entities if node.entity_id.year == year]
    return []


@classmethod
def _get_all_identities(cls) -> Set['ProgramTreeIdentity']:
    result = set()
    for tree in cls.root_entities:
        identities = {program_tree.ProgramTreeIdentity(node.code, node.year) for node in tree.get_all_nodes()
                      if not node.is_learning_unit()}
        result.union(identities)
    return result

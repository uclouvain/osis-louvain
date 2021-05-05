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
from typing import List, Type, Optional

from osis_common.ddd import interface
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception, program_tree
from program_management.ddd.repositories import node as node_repository, program_tree as tree_repository, \
    program_tree_version as tree_version_repository


class FakeNodeRepository(node_repository.NodeRepository):
    _nodes = list()  # type: List[Node]

    @classmethod
    def create(cls, node: 'Node', **_) -> 'NodeIdentity':
        cls._nodes.append(node)
        return node.entity_id

    @classmethod
    def update(cls, node: 'Node', **_) -> 'NodeIdentity':
        if node not in cls._nodes:
            raise exception.NodeNotFoundException()
        return node.entity_id

    @classmethod
    def get(cls, node_id: 'NodeIdentity') -> Optional['Node']:
        result = next((node for node in cls._nodes if node.entity_id == node_id), None)
        if not result:
            raise exception.NodeNotFoundException()
        return result

    @classmethod
    def search(cls, node_ids: List['NodeIdentity'] = None, year: int = None, **kwargs) -> List['Node']:
        if node_ids:
            return [node for node in cls._nodes if node.entity_id in node_ids]
        if year:
            return [node for node in cls._nodes if node.entity_id.year == year]
        return []

    @classmethod
    def delete(cls, node_id: 'NodeIdentity', **_) -> None:
        node_to_delete = next((node for node in cls._nodes if node.entity_id == node_id), None)
        if node_to_delete:
            cls._nodes.remove(node_to_delete)


class FakeProgramTreeRepository(tree_repository.ProgramTreeRepository):
    _trees = list()  # type: List[ProgramTree]

    @classmethod
    def create(
            cls,
            program_tree: 'ProgramTree',
            create_orphan_group_service: interface.ApplicationService = None,
            copy_group_service: interface.ApplicationService = None,
    ) -> 'ProgramTreeIdentity':
        cls._trees.append(program_tree)
        return program_tree.entity_id

    @classmethod
    def update(cls, program_tree: 'ProgramTree', **_) -> 'ProgramTreeIdentity':
        if program_tree not in cls._trees:
            raise exception.ProgramTreeNotFoundException()
        return program_tree.entity_id

    @classmethod
    def get(cls, entity_id: 'ProgramTreeIdentity') -> 'ProgramTree':
        result = next((tree for tree in cls._trees if tree.entity_id == entity_id), None)
        if not result:
            raise exception.ProgramTreeNotFoundException()
        return result

    @classmethod
    def search(
            cls,
            entity_ids: Optional[List['ProgramTreeIdentity']] = None,
            root_ids: List[int] = None
    ) -> List['ProgramTree']:
        result = []
        if entity_ids:
            return [root_entity for root_entity in cls._trees if root_entity.entity_id in entity_ids]
        return result

    @classmethod
    def search_from_children(cls, node_ids: List['NodeIdentity'], **kwargs) -> List['ProgramTree']:
        result = []
        set_node_ids = set(node_ids)
        for tree in cls._trees:
            children_nodes = tree.get_all_nodes() - {tree.root_node}
            children_nodes_ids = set([node.entity_id for node in children_nodes])
            if not children_nodes_ids.isdisjoint(set_node_ids):
                result.append(tree)
        return result

    @classmethod
    def get_all_identities(cls) -> List['ProgramTreeIdentity']:
        result = set()
        for tree in cls._trees:
            identities = {program_tree.ProgramTreeIdentity(node.code, node.year) for node in tree.get_all_nodes()
                          if not node.is_learning_unit()}
            result.union(identities)
        return list(result)

    @classmethod
    def delete(
            cls,
            entity_id: 'ProgramTreeIdentity',
            delete_node_service: interface.ApplicationService = None,
    ) -> None:
        program_tree = cls.get(entity_id)
        nodes = program_tree.get_all_nodes()

        idx = -1
        for idx, entity in enumerate(cls._trees):
            if entity.entity_id == entity_id:
                break
        if idx >= 0:
            cls._trees.pop(idx)

        for node in nodes:
            cmd = command.DeleteNodeCommand(code=node.code, year=node.year, node_type=node.node_type.name,
                                            acronym=node.title)
            delete_node_service(cmd)


class FakeProgramTreeVersionRepository(tree_version_repository.ProgramTreeVersionRepository):
    _trees_version = list()  # type: List[ProgramTreeVersion]

    @classmethod
    def create(
            cls,
            program_tree_version: 'ProgramTreeVersion',
            **_
    ) -> 'ProgramTreeVersionIdentity':
        cls._trees_version.append(program_tree_version)
        return program_tree_version.entity_id

    @classmethod
    def update(cls, program_tree_version: 'ProgramTreeVersion', **_) -> 'ProgramTreeVersionIdentity':
        if program_tree_version not in cls._trees_version:
            raise exception.ProgramTreeVersionNotFoundException()
        return program_tree_version.entity_id

    @classmethod
    def get(cls, entity_id: 'ProgramTreeVersionIdentity') -> 'ProgramTreeVersion':
        result = next((tree for tree in cls._trees_version if tree.entity_id == entity_id), None)
        if not result:
            raise exception.ProgramTreeVersionNotFoundException()
        return result

    @classmethod
    def search(
            cls,
            entity_ids: Optional[List['ProgramTreeVersionIdentity']] = None,
            version_name: str = None,
            offer_acronym: str = None,
            transition_name: str = None,
            code: str = None,
            year: int = None,
            **kwargs
    ) -> List['ProgramTreeVersion']:
        result = cls._trees_version  # type: List[ProgramTreeVersion]
        if entity_ids:
            result = (tree_version for tree_version in result if tree_version.entity_id in entity_ids)
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
    def search_versions_from_trees(cls, trees: List['ProgramTree']) -> List['ProgramTreeVersion']:
        tree_entities = {tree.entity_id for tree in trees}
        return [tree_version for tree_version in cls._trees_version if tree_version.tree.entity_id in tree_entities]

    @classmethod
    def delete(
           cls,
           entity_id: 'ProgramTreeVersionIdentity',
           delete_program_tree_service: interface.ApplicationService = None
    ) -> None:
        tree_version = cls.get(entity_id)

        idx = -1
        for idx, entity in enumerate(cls._trees_version):
            if entity.entity_id == entity_id:
                break
        if idx >= 0:
            cls._trees_version.pop(idx)

        cmd = command.DeleteProgramTreeCommand(
            code=tree_version.tree.entity_id.code,
            year=tree_version.tree.entity_id.year
        )
        delete_program_tree_service(cmd)


def get_fake_node_repository(root_entities: List['Node']) -> Type['FakeNodeRepository']:
    FakeNodeRepository._nodes = root_entities
    return FakeNodeRepository


def get_fake_program_tree_repository(root_entities: List['ProgramTree']) -> Type['FakeProgramTreeRepository']:
    FakeProgramTreeRepository._trees = root_entities
    return FakeProgramTreeRepository


def get_fake_program_tree_version_repository(
        root_entities: List['ProgramTreeVersion']
) -> Type['FakeProgramTreeVersionRepository']:
    FakeProgramTreeVersionRepository._trees_version = root_entities
    return FakeProgramTreeVersionRepository

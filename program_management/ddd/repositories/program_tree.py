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
from typing import Optional, List, Union

from django.db.models import Q

from base.models.group_element_year import GroupElementYear
from education_group.ddd.command import CreateOrphanGroupCommand, CopyGroupCommand
from osis_common.ddd import interface
from osis_common.ddd.interface import Entity
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception
from program_management.ddd.repositories import persist_tree, load_tree, node
from program_management.models.element import Element


class ProgramTreeRepository(interface.AbstractRepository):

    @classmethod
    def search(
            cls,
            entity_ids: Optional[List['ProgramTreeIdentity']] = None,
            root_ids: List[int] = None
    ) -> List['ProgramTree']:
        if entity_ids:
            root_ids = _search_root_ids(entity_ids)
        if root_ids:
            return load_tree.load_trees(root_ids)
        return []

    @classmethod
    def search_from_children(cls, node_ids: List['NodeIdentity'], **kwargs) -> List['ProgramTree']:
        nodes = node.NodeRepository.search(entity_ids=node_ids)
        node_db_ids = [n.node_id for n in nodes]
        return load_tree.load_trees_from_children(node_db_ids, **kwargs)

    @classmethod
    def delete(
            cls,
            entity_id: 'ProgramTreeIdentity',
            delete_node_service: interface.ApplicationService = None,
    ) -> None:
        program_tree = cls.get(entity_id)

        _delete_node_content(program_tree.root_node, delete_node_service)
        cmd = command.DeleteNodeCommand(
            code=program_tree.root_node.code,
            year=program_tree.root_node.year,
            node_type=program_tree.root_node.node_type.name,
            acronym=program_tree.root_node.title
        )
        delete_node_service(cmd)

    @classmethod
    def create(
            cls,
            program_tree: 'ProgramTree',
            create_orphan_group_service: interface.ApplicationService = None,
            copy_group_service: interface.ApplicationService = None,
    ) -> 'ProgramTreeIdentity':
        for node in [n for n in program_tree.get_all_nodes() if n._has_changed and not n.is_learning_unit()]:
            if create_orphan_group_service:
                create_orphan_group_service(
                    CreateOrphanGroupCommand(
                        code=node.code,
                        year=node.year,
                        type=node.node_type.name,
                        abbreviated_title=node.title,
                        title_fr=node.group_title_fr,
                        title_en=node.group_title_en,
                        credits=int(node.credits) if node.credits else None,
                        constraint_type=node.constraint_type.name if node.constraint_type else None,
                        min_constraint=node.min_constraint,
                        max_constraint=node.max_constraint,
                        management_entity_acronym=node.management_entity_acronym,
                        teaching_campus_name=node.teaching_campus.name,
                        organization_name=node.teaching_campus.university_name,
                        remark_fr=node.remark_fr or "",
                        remark_en=node.remark_en or "",
                        start_year=node.start_year,
                        end_year=node.end_year,
                    )
                )
            if copy_group_service:
                copy_group_service(
                    CopyGroupCommand(
                        from_code=node.code,
                        from_year=node.year - 1,
                    )
                )

        persist_tree.persist(program_tree)
        return program_tree.entity_id

    @classmethod
    def update(cls, program_tree: 'ProgramTree', **_) -> 'ProgramTreeIdentity':
        persist_tree.persist(program_tree)
        return program_tree.entity_id

    @classmethod
    def get(cls, entity_id: 'ProgramTreeIdentity') -> 'ProgramTree':
        try:
            tree_root_id = Element.objects.get(
                group_year__partial_acronym=entity_id.code,
                group_year__academic_year__year=entity_id.year
            ).pk
            return load_tree.load(tree_root_id)
        except Element.DoesNotExist:
            raise exception.ProgramTreeNotFoundException(code=entity_id.code, year=entity_id.year)


def _delete_node_content(parent_node: 'Node', delete_node_service: interface.ApplicationService) -> None:
    for link in parent_node.children:
        child_node = link.child
        GroupElementYear.objects.filter(pk=link.pk).delete()
        try:
            cmd = command.DeleteNodeCommand(
                code=child_node.code,
                year=child_node.year,
                node_type=child_node.node_type.name,
                acronym=child_node.title
            )
            delete_node_service(cmd)
        except exception.NodeIsUsedException:
            continue
        _delete_node_content(link.child, delete_node_service)


def _search_root_ids(entity_ids: List['ProgramTreeIdentity']) -> List[int]:
    qs = Element.objects.all()
    filter_search_from = _build_where_clause(entity_ids[0])
    for identity in entity_ids[1:]:
        filter_search_from |= _build_where_clause(identity)
    qs = qs.filter(filter_search_from)
    return list(qs.values_list('pk', flat=True))


def _build_where_clause(node_identity: 'ProgramTreeIdentity') -> Q:
    return Q(
        group_year__partial_acronym=node_identity.code,
        group_year__academic_year__year=node_identity.year
    )

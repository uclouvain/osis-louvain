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
from typing import Optional, List

from base.models.group_element_year import GroupElementYear
from education_group.ddd.command import CreateOrphanGroupCommand
from osis_common.ddd import interface
from osis_common.ddd.interface import Entity
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception
from program_management.ddd.repositories import persist_tree, load_tree, node
from program_management.models.element import Element


class ProgramTreeRepository(interface.AbstractRepository):

    @classmethod
    def search(cls, entity_ids: Optional[List['ProgramTreeIdentity']] = None, **kwargs) -> List[Entity]:
        raise NotImplementedError

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
        links = program_tree.get_all_links()
        nodes = program_tree.get_all_nodes()

        GroupElementYear.objects.filter(pk__in=(link.pk for link in links)).delete()

        for node in nodes:
            cmd = command.DeleteNodeCommand(code=node.code, year=node.year, node_type=node.node_type.name)
            delete_node_service(cmd)

    @classmethod
    def create(
            cls,
            program_tree: 'ProgramTree',
            create_group_service: interface.ApplicationService = None
    ) -> 'ProgramTreeIdentity':
        for child_node in [n for n in program_tree.get_all_nodes() if n._has_changed is True]:
            create_group_service(
                CreateOrphanGroupCommand(
                    code=child_node.code,
                    year=child_node.year,
                    type=child_node.node_type.name,
                    abbreviated_title=child_node.title,
                    title_fr=child_node.group_title_fr,
                    title_en=child_node.group_title_en,
                    credits=int(child_node.credits) if child_node.credits else None,
                    constraint_type=child_node.constraint_type.name if child_node.constraint_type else None,
                    min_constraint=child_node.min_constraint,
                    max_constraint=child_node.max_constraint,
                    management_entity_acronym=child_node.management_entity_acronym,
                    teaching_campus_name=child_node.teaching_campus.name,
                    organization_name=child_node.teaching_campus.university_name,
                    remark_fr=child_node.remark_fr or "",
                    remark_en=child_node.remark_en or "",
                    start_year=child_node.start_year,
                    end_year=child_node.end_year,
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
            raise exception.ProgramTreeNotFoundException()

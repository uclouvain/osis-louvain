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
from typing import Optional, List, Dict, Any

from django.db import transaction
from django.db.models import Q

from base.models import group_element_year
from base.models.enums.link_type import LinkTypes
from base.models.enums.quadrimesters import DerogationQuadrimester
from base.models.group_element_year import GroupElementYear
from education_group.ddd.command import CreateOrphanGroupCommand, CopyGroupCommand
from osis_common.ddd import interface
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception, program_tree
from program_management.ddd.domain.exception import ProgramTreeNotFoundException
from program_management.ddd.domain.link import factory as link_factory, LinkIdentity
from program_management.ddd.domain.prerequisite import NullPrerequisites
from program_management.ddd.repositories import _persist_prerequisite
from program_management.ddd.repositories import persist_tree, node, load_node, load_authorized_relationship, \
    tree_prerequisites
from program_management.models.element import Element

# Typing
LinkKey = str  # <parent_id>_<child_id>  Example : "123_124"
NodeKey = int  # Element.pk
GroupElementYearColumnName = str
TreeStructure = List[Dict[GroupElementYearColumnName, Any]]


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
            return _load_trees(root_ids)
        return []

    @classmethod
    def search_from_children(cls, node_ids: List['NodeIdentity'], **kwargs) -> List['ProgramTree']:
        nodes = node.NodeRepository.search(entity_ids=node_ids)
        node_db_ids = [n.node_id for n in nodes]
        return _load_trees_from_children(node_db_ids, **kwargs)

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

        cls.__persist(program_tree)
        return program_tree.entity_id

    @classmethod
    def update(cls, program_tree: 'ProgramTree', **_) -> 'ProgramTreeIdentity':
        cls.__persist(program_tree)
        return program_tree.entity_id

    @classmethod
    @transaction.atomic
    def __persist(cls, tree: 'ProgramTree') -> None:
        persist_tree._update_or_create_links(tree)
        persist_tree._delete_links(tree, tree.root_node)
        _persist_prerequisite.persist(tree)

    @classmethod
    def get(cls, entity_id: 'ProgramTreeIdentity') -> 'ProgramTree':
        try:
            tree_root_id = Element.objects.get(
                group_year__partial_acronym=entity_id.code,
                group_year__academic_year__year=entity_id.year
            ).pk
            return _load(tree_root_id)
        except Element.DoesNotExist:
            raise exception.ProgramTreeNotFoundException(code=entity_id.code, year=entity_id.year)


def _load(tree_root_id: int) -> 'ProgramTree':
    trees = _load_trees([tree_root_id])
    if not trees:
        raise ProgramTreeNotFoundException
    return trees[0]


def _load_trees(tree_root_ids: List[int]) -> List['ProgramTree']:
    trees = []
    structure = group_element_year.GroupElementYear.objects.get_adjacency_list(tree_root_ids)
    nodes = _load_tree_nodes(structure)
    links = _load_tree_links(structure)
    prerequisites_of_all_trees = tree_prerequisites.TreePrerequisitesRepository().search(
        tree_root_ids=tree_root_ids
    )
    root_nodes = load_node.load_multiple(tree_root_ids)
    nodes.update({n.pk: n for n in root_nodes})
    for root_node in root_nodes:
        tree_root_id = root_node.pk
        structure_for_current_root_node = [s for s in structure if s['starting_node_id'] == tree_root_id]
        tree = _build_tree(root_node, structure_for_current_root_node, nodes, links,
                           prerequisites_of_all_trees)
        trees.append(tree)
    return trees


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


def _load_tree_nodes(tree_structure: TreeStructure) -> Dict[NodeKey, 'Node']:
    element_ids = [link['child_id'] for link in tree_structure]
    nodes_list = load_node.load_multiple(element_ids)
    return {n.pk: n for n in nodes_list}


def _load_tree_links(tree_structure: TreeStructure) -> Dict[LinkKey, 'Link']:
    group_element_year_ids = [link['id'] for link in tree_structure]
    group_element_year_qs = group_element_year.GroupElementYear.objects.filter(pk__in=group_element_year_ids).values(
        'pk',
        'relative_credits',
        'min_credits',
        'max_credits',
        'access_condition',
        'is_mandatory',
        'block',
        'comment',
        'comment_english',
        'own_comment',
        'quadrimester_derogation',
        'link_type',
        'parent_element_id',
        'child_element_id',
        'order'
    )

    tree_links = {}
    for gey_dict in group_element_year_qs:
        parent_id = gey_dict.pop('parent_element_id')
        child_id = gey_dict.pop('child_element_id')
        __convert_link_type_to_enum(gey_dict)
        __convert_quadrimester_to_enum(gey_dict)

        tree_id = '_'.join([str(parent_id), str(child_id)])
        tree_links[tree_id] = link_factory.get_link(parent=None, child=None, **gey_dict)
    return tree_links


def __convert_link_type_to_enum(link_data: dict) -> None:
    link_type = link_data['link_type']
    if link_type:
        link_data['link_type'] = LinkTypes[link_type]


def __convert_quadrimester_to_enum(gey_dict: dict) -> None:
    if gey_dict.get('quadrimester_derogation'):
        gey_dict['quadrimester_derogation'] = DerogationQuadrimester[gey_dict['quadrimester_derogation']]


def _build_tree(
        root_node: 'Node',
        tree_structure: TreeStructure,
        nodes: Dict[NodeKey, 'Node'],
        links: Dict[LinkKey, 'Link'],
        prerequisites_of_all_trees: List['Prerequisites']
) -> 'ProgramTree':
    structure_by_parent = {}  # For performance
    for s_dict in tree_structure:
        if s_dict['path']:  # TODO :: Case child_id or parent_id is null - to remove after DB null constraint set
            parent_path = '|'.join(s_dict['path'].split('|')[:-1])
            structure_by_parent.setdefault(parent_path, []).append(s_dict)
    root_node.children = __build_children(str(root_node.pk), structure_by_parent, nodes, links)
    tree = program_tree.ProgramTree(
        root_node,
        authorized_relationships=load_authorized_relationship.load(),
    )
    tree.prerequisites = next(
        (prereq for prereq in prerequisites_of_all_trees if prereq.context_tree == tree.entity_id),
        NullPrerequisites(context_tree=tree.entity_id)
    )
    return tree


def __build_children(
        root_path: 'Path',
        map_parent_path_with_tree_structure: Dict['Path', TreeStructure],
        nodes: Dict[NodeKey, 'Node'],
        links: Dict[LinkKey, 'Link']
) -> List['Link']:
    children = []
    for child_structure in map_parent_path_with_tree_structure.get(root_path) or []:
        child_id = child_structure['child_id']
        parent_id = child_structure['parent_id']
        child_node = nodes[child_id]

        if not child_node.children:
            # "if" condition for performance : avoid recursivity if the children of the node have already been computed
            child_node.children = __build_children(
                child_structure['path'],
                map_parent_path_with_tree_structure,
                nodes,
                links
            )

        link_node = links['_'.join([str(parent_id), str(child_node.pk)])]

        link_node.parent = nodes[parent_id]
        link_node.child = child_node
        link_node.entity_id = LinkIdentity(
            parent_code=link_node.parent.code,
            child_code=link_node.child.code,
            parent_year=link_node.parent.year,
            child_year=link_node.child.year
        )
        children.append(link_node)
    return children


def _get_root_ids(child_element_ids: list, link_type: LinkTypes = None) -> List[int]:
    if child_element_ids:
        assert isinstance(child_element_ids, list)
    if not child_element_ids:
        return []

    qs = group_element_year.GroupElementYear.objects.get_reverse_adjacency_list(
        child_element_ids=child_element_ids,
        link_type=link_type,
    )
    if not qs:
        return []
    all_parents = set(obj["parent_id"] for obj in qs)
    parent_by_child = {
        obj["child_id"]: obj["parent_id"] for obj in qs
    }
    return set(
        parent_id for parent_id in all_parents
        if not parent_by_child.get(parent_id)
    )


def _load_trees_from_children(child_element_ids: list, link_type: LinkTypes = None) -> List['ProgramTree']:
    root_ids = _get_root_ids(child_element_ids, link_type)
    return _load_trees(list(root_ids))

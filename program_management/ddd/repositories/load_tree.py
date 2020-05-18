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

from typing import List, Dict, Any

from django.db.models import Case, F, When, IntegerField

from base.models import group_element_year
from base.models.enums.link_type import LinkTypes
from base.models.enums.quadrimesters import DerogationQuadrimester
from osis_common.decorators.deprecated import deprecated
from program_management.ddd.business_types import *
from program_management.ddd.domain.link import factory as link_factory
from program_management.ddd.domain.prerequisite import NullPrerequisite
from program_management.ddd.domain.prerequisite import Prerequisite
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.repositories import load_node, load_prerequisite, \
    load_authorized_relationship
# Typing
from program_management.ddd.repositories.load_prerequisite import TreeRootId, NodeId
from program_management.models.enums.node_type import NodeType

GroupElementYearColumnName = str
LinkKey = str  # <parent_id>_<child_id>  Example : "123_124"
NodeKey = str  # <node_id>_<node_type> Example : "589_LEARNING_UNIT"
TreeStructure = List[Dict[GroupElementYearColumnName, Any]]


@deprecated  # use ProgramTreeRepository.get() instead
def load(tree_root_id: int) -> 'ProgramTree':
    return load_trees([tree_root_id])[0]


@deprecated  # use ProgramTreeRepository.search() instead
def load_trees(tree_root_ids: List[int]) -> List['ProgramTree']:
    trees = []
    structure = group_element_year.GroupElementYear.objects.get_adjacency_list(tree_root_ids)
    nodes = __load_tree_nodes(structure)
    links = __load_tree_links(structure)
    has_prerequisites = load_prerequisite.load_has_prerequisite_multiple(tree_root_ids, nodes)
    is_prerequisites = load_prerequisite.load_is_prerequisite_multiple(tree_root_ids, nodes)
    for tree_root_id in tree_root_ids:
        root_node = load_node.load_node_education_group_year(tree_root_id)  # TODO : use load_multiple
        unique_key = '{}_{}'.format(root_node.pk, NodeType.EDUCATION_GROUP)
        nodes[unique_key] = root_node
        tree_prerequisites = {
            'has_prerequisite_dict': has_prerequisites.get(tree_root_id) or {},
            'is_prerequisite_dict': is_prerequisites.get(tree_root_id) or {},
        }
        structure_for_current_root_node = [s for s in structure if s['starting_node_id'] == tree_root_id]
        tree = __build_tree(root_node, structure_for_current_root_node, nodes, links, tree_prerequisites)
        trees.append(tree)
        del nodes[unique_key]
    return trees


# FIXME :: to move into ProgramTreeRepository.search()
def load_trees_from_children(
        child_branch_ids: list,
        child_leaf_ids: list = None,
        link_type: LinkTypes = None
) -> List['ProgramTree']:
    if not child_branch_ids and not child_leaf_ids:
        return []
    if child_branch_ids:
        assert isinstance(child_branch_ids, list)
    if child_leaf_ids:
        assert isinstance(child_leaf_ids, list)

    qs = group_element_year.GroupElementYear.objects.get_reverse_adjacency_list(
        child_branch_ids=child_branch_ids,
        child_leaf_ids=child_leaf_ids,
        link_type=link_type,
    )
    if not qs:
        return []
    all_parents = set(obj["parent_id"] for obj in qs)
    parent_by_child_branch = {
        obj["child_id"]: obj["parent_id"] for obj in qs
    }
    root_ids = set(
        parent_id for parent_id in all_parents
        if not parent_by_child_branch.get(parent_id)
    )
    return load_trees(list(root_ids))


def __load_tree_nodes(tree_structure: TreeStructure) -> Dict[NodeKey, 'Node']:
    ids = [link['id'] for link in tree_structure]
    nodes_list = load_node.load_multiple(ids)
    return {'{}_{}'.format(n.pk, n.type): n for n in nodes_list}


def __convert_link_type_to_enum(link_data: dict) -> None:
    link_type = link_data['link_type']
    if link_type:
        link_data['link_type'] = LinkTypes[link_type]


def __convert_quadrimester_to_enum(gey_dict: dict) -> None:
    if gey_dict.get('quadrimester'):
        gey_dict['quadrimester'] = DerogationQuadrimester[gey_dict['quadrimester']]


def __load_tree_links(tree_structure: TreeStructure) -> Dict[LinkKey, 'Link']:
    group_element_year_ids = [link['id'] for link in tree_structure]
    group_element_year_qs = group_element_year.GroupElementYear.objects.filter(pk__in=group_element_year_ids).annotate(
        child_id=Case(
            When(child_branch_id__isnull=True, then=F('child_leaf_id')),
            default=F('child_branch_id'),
            output_field=IntegerField()
        )
    ).values(
        'pk',
        'relative_credits',
        'min_credits',
        'max_credits',
        'is_mandatory',
        'block',
        'comment',
        'comment_english',
        'own_comment',
        'quadrimester_derogation',
        'link_type',
        'parent_id',
        'child_id',
        'order'
    )

    tree_links = {}
    for gey_dict in group_element_year_qs:
        parent_id = gey_dict.pop('parent_id')
        child_id = gey_dict.pop('child_id')
        __convert_link_type_to_enum(gey_dict)
        __convert_quadrimester_to_enum(gey_dict)

        tree_id = '_'.join([str(parent_id), str(child_id)])
        tree_links[tree_id] = link_factory.get_link(parent=None, child=None, **gey_dict)
    return tree_links


def __load_tree_prerequisites(
        tree_root_ids: List[int],
        nodes: Dict[NodeKey, 'Node']
) -> Dict[str, Dict[TreeRootId, Dict[NodeId, Prerequisite]]]:
    return {
        'has_prerequisite_dict': load_prerequisite.load_has_prerequisite_multiple(tree_root_ids, nodes),
        'is_prerequisite_dict': load_prerequisite.load_is_prerequisite_multiple(tree_root_ids, nodes)
    }


def __build_tree(
        root_node: 'Node',
        tree_structure: TreeStructure,
        nodes: Dict[NodeKey, 'Node'],
        links: Dict[LinkKey, 'Link'],
        prerequisites
) -> 'ProgramTree':
    structure_by_parent = {}  # For performance
    for s_dict in tree_structure:
        if s_dict['path']:  # TODO :: Case child_id or parent_id is null - to remove after DB null constraint set
            parent_path = '|'.join(s_dict['path'].split('|')[:-1])
            structure_by_parent.setdefault(parent_path, []).append(s_dict)
    root_node.children = __build_children(str(root_node.pk), structure_by_parent, nodes, links, prerequisites)
    tree = ProgramTree(root_node, authorized_relationships=load_authorized_relationship.load())
    return tree


def __build_children(
        root_path: 'Path',
        map_parent_path_with_tree_structure: Dict['Path', TreeStructure],
        nodes: Dict[NodeKey, 'Node'],
        links: Dict[LinkKey, 'Link'],
        prerequisites
) -> List['Link']:
    children = []
    for child_structure in map_parent_path_with_tree_structure.get(root_path) or []:
        child_id = child_structure['child_id']
        parent_id = child_structure['parent_id']
        if not child_id or not parent_id:
            continue  # TODO :: To remove when child_leaf and child_branch will disappear !
        ntype = NodeType.LEARNING_UNIT if child_structure['child_leaf_id'] else NodeType.EDUCATION_GROUP
        child_node = nodes['{}_{}'.format(child_id, ntype)]
        child_node.children = __build_children(
            child_structure['path'],
            map_parent_path_with_tree_structure,
            nodes,
            links,
            prerequisites
        )

        if child_node.is_learning_unit():
            child_node.prerequisite = prerequisites['has_prerequisite_dict'].get(child_node.pk, NullPrerequisite())
            child_node.is_prerequisite_of = prerequisites['is_prerequisite_dict'].get(child_node.pk, [])

        link_node = links['_'.join([str(parent_id), str(child_id)])]
        link_node.parent = nodes['{}_{}'.format(parent_id, NodeType.EDUCATION_GROUP)]
        link_node.child = child_node
        children.append(link_node)
    return children

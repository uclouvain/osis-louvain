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
from program_management.ddd.business_types import *
from program_management.ddd.domain import node
from program_management.ddd.domain.link import factory as link_factory
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.repositories import load_node, load_prerequisite, \
    load_authorized_relationship
# Typing
from program_management.models.enums.node_type import NodeType

GroupElementYearColumnName = str
LinkKey = str  # <parent_id>_<child_id>  Example : "123_124"
NodeKey = str  # <node_id>_<node_type> Example : "589_LEARNING_UNIT"
TreeStructure = List[Dict[GroupElementYearColumnName, Any]]


def load(tree_root_id: int) -> 'ProgramTree':
    root_node = load_node.load_node_education_group_year(tree_root_id)

    structure = group_element_year.GroupElementYear.objects.get_adjacency_list([tree_root_id])
    nodes = __load_tree_nodes(structure)
    nodes.update({'{}_{}'.format(root_node.pk, NodeType.EDUCATION_GROUP): root_node})
    links = __load_tree_links(structure)
    prerequisites = __load_tree_prerequisites(tree_root_id, nodes)
    return __build_tree(root_node, structure, nodes, links, prerequisites)


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
    # TODO :: performance (get all trees in one single query)
    return [load(root_id) for root_id in root_ids]


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


def __load_tree_prerequisites(tree_root_id: int, nodes: dict):
    node_leaf_ids = [n.pk for n in nodes.values() if isinstance(n, node.NodeLearningUnitYear)]
    has_prerequisite_dict = load_prerequisite.load_has_prerequisite(tree_root_id, node_leaf_ids)
    is_prerequisite_dict = {
        main_node_id: [nodes['{}_{}'.format(id, NodeType.LEARNING_UNIT)] for id in node_ids]
        for main_node_id, node_ids in load_prerequisite.load_is_prerequisite(tree_root_id, node_leaf_ids).items()
    }
    return {'has_prerequisite_dict': has_prerequisite_dict, 'is_prerequisite_dict': is_prerequisite_dict}


def __build_tree(
        root_node: 'Node',
        tree_structure: TreeStructure,
        nodes: Dict[NodeKey, 'Node'],
        links: Dict[LinkKey, 'Link'],
        prerequisites
) -> 'ProgramTree':
    root_node.children = __build_children(str(root_node.pk), tree_structure, nodes, links, prerequisites)
    tree = ProgramTree(root_node, authorized_relationships=load_authorized_relationship.load())
    return tree


def __build_children(
        root_path: 'Path',
        tree_structure: TreeStructure,
        nodes: Dict[NodeKey, 'Node'],
        links: Dict[LinkKey, 'Link'],
        prerequisites
) -> List['Link']:
    children = []

    childs_structure = [
        structure for structure in tree_structure
        if structure['path'] == "|".join([root_path, str(structure['child_id'])])
    ]
    for child_structure in childs_structure:
        child_id = child_structure['child_id']
        ntype = NodeType.LEARNING_UNIT if child_structure['child_leaf_id'] else NodeType.EDUCATION_GROUP
        child_node = nodes['{}_{}'.format(child_id, ntype)]
        child_node.children = __build_children(
            "|".join([root_path, str(child_node.pk)]),
            tree_structure,
            nodes,
            links,
            prerequisites
        )

        if isinstance(child_node, node.NodeLearningUnitYear):
            child_node.prerequisite = prerequisites['has_prerequisite_dict'].get(child_node.pk, [])
            child_node.is_prerequisite_of = prerequisites['is_prerequisite_dict'].get(child_node.pk, [])

        parent_id = child_structure['parent_id']
        link_node = links['_'.join([str(parent_id), str(child_id)])]
        link_node.parent = nodes['{}_{}'.format(parent_id, NodeType.EDUCATION_GROUP)]
        link_node.child = child_node
        children.append(link_node)
    return children

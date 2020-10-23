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
from collections import defaultdict

from typing import Dict, List, Any

from django.urls import reverse

from program_management.ddd.business_types import *
from program_management.ddd.domain.node import NodeGroupYear, NodeIdentity
from program_management.ddd.service.read import search_program_trees_using_node_service

from program_management.ddd.command import GetProgramTreesFromNodeCommand
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.serializers.node_view import get_program_tree_version_name, get_program_tree_version_title, \
    get_program_tree_version_dict
from program_management.ddd.domain.program_tree import get_nearest_parents
from program_management.ddd.domain.service.identity_search import ProgramTreeIdentitySearch


def get_utilizations(node_identity: 'NodeIdentity', language: str) -> List[Dict[str, Any]]:
    cmd = GetProgramTreesFromNodeCommand(code=node_identity.code, year=node_identity.year)
    program_trees = search_program_trees_using_node_service.search_program_trees_using_node(cmd)

    utilization_rows_dict = defaultdict(list)
    parent_nodes = []

    for tree in program_trees:
        for path, child_node in tree.root_node.descendents.items():
            if child_node.entity_id == node_identity:
                links = tree.get_links_using_node(child_node)
                for link in links:
                    if link.parent not in parent_nodes:
                        parent_nodes.append(link.parent)
                        _build_parents_info(link, program_trees, utilization_rows_dict)

    return _buid_utilization_rows(utilization_rows_dict, language)


def _buid_utilization_rows(utilization_rows_dict: Dict['Link', List['Node']], language: str) -> List[Dict[str, Any]]:
    utilization_rows = []

    for link, training_nodes in utilization_rows_dict.items():
        utilization_in_trainings = defaultdict(list)
        if len(training_nodes) > 0:
            for utilization in training_nodes:
                root_node = utilization.get('root_node')
                direct_parent = utilization.get('parent_direct_node')
                key = direct_parent if direct_parent else root_node
                if key:
                    used_trainings = utilization_in_trainings[key]
                    if root_node and key != root_node and root_node not in used_trainings:
                        used_trainings.append(root_node)
                        utilization_in_trainings[key] = used_trainings
        elif (link.parent.is_minor_or_deepening()) or (link.parent.is_training() and link.parent.is_finality()):
            utilization_in_trainings = {link.parent: []}

        version_details = get_program_tree_version_dict(
            ProgramTreeVersionRepository.search(code=link.parent.code, year=link.parent.year), language
        )
        utilization_rows.append(
            {
                'link': link,
                'version_details': version_details,
                'training_nodes': _get_training_nodes(utilization_in_trainings)
            }
        )
    return sorted(utilization_rows, key=lambda row: row['link'].parent.code)


def _get_training_nodes(dd: Dict['NodeGroupYear', List['NodeGroupYear']]) -> List[Dict[str, Any]]:
    training_nodes = []
    for direct_parent, main_root_nodes in dd.items():
        root_nodes = []
        for root_node in main_root_nodes:
            root_nodes.append(
                {
                    'root': root_node,
                    'version_name': _get_version_name(root_node),
                    'url': _get_identification_url(root_node)
                }
            )

        training_nodes.append(
            {
                'direct_gathering': {'parent': direct_parent, 'url': _get_identification_url(direct_parent)},
                'root_nodes': sorted(root_nodes, key=lambda row: row['root'].title),
                'version_name': _get_version_name(direct_parent)
            }
        )
    return sorted(training_nodes, key=lambda row: row['direct_gathering']['parent'].title)


def _get_version_name(direct_parent):
    parent_node_identity = NodeIdentity(code=direct_parent.code, year=direct_parent.year)
    version_name = get_program_tree_version_name(
        parent_node_identity,
        ProgramTreeVersionRepository.search_all_versions_from_root_node(parent_node_identity)
    )
    return version_name


def _get_identification_url(node: 'Node'):
    return reverse('element_identification', kwargs={'code': node.code, 'year': node.year})


def _build_parents_info(link: 'Link',
                        parent_node_pgm_trees:  List['ProgramTree'],
                        utilization_rows_dict: Dict['link', Dict[str, 'Node']]):
    found = False
    for parent_tree in parent_node_pgm_trees:
        for path, child_node in parent_tree.root_node.descendents.items():
            if isinstance(child_node, NodeGroupYear) and child_node == link.parent:
                found = True
                gathering = get_nearest_parents(parent_tree.get_parents(path))
                lk_to_update = utilization_rows_dict[link]
                if gathering:
                    lk_to_update.append(gathering)
                    utilization_rows_dict[link] = lk_to_update
    if not found:
        lk_to_update = utilization_rows_dict.get(link, [])
        if link.parent not in lk_to_update:
            utilization_rows_dict[link] = lk_to_update

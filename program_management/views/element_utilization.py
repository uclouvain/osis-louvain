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
from typing import Dict, List, Any

from django.urls import reverse

from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command
from program_management.ddd.service.read import search_tree_versions_using_node_service
from program_management.serializers.node_view import get_program_tree_version_name
from program_management.views.generic import LearningUnitGeneric
from program_management.serializers.node_view import get_program_tree_version_name
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.business_types import *
from program_management.ddd.domain.node import NodeLearningUnitYear, NodeGroupYear, NodeIdentity
from program_management.ddd.service.read import search_program_trees_using_node_service
from program_management.ddd.domain.program_tree_version import ProgramTreeVersion
from program_management.ddd.command import GetProgramTreesFromNodeCommand


class LearningUnitUtilization(PermissionRequiredMixin, LearningUnitGeneric):
    template_name = "learning_unit/tab_utilization.html"

    permission_required = 'base.view_educationgroup'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cmd = GetProgramTreesFromNodeCommand(code=self.node.code, year=self.node.year)
        program_trees = search_program_trees_using_node_service.search_program_trees_using_node(cmd)
        cmd = command.GetProgramTreesVersionFromNodeCommand(code=self.node.code, year=self.node.year)
        program_trees_versions = search_tree_versions_using_node_service.search_tree_versions_using_node(cmd)
        for program_tree_version in program_trees_versions:
            tree = program_tree_version.get_tree()
            program_trees.append(tree)
        context['utilization_rows'] = get_utilization_rows(program_trees, self.node)
        return context


def get_utilization_rows(program_trees_versions: List['ProgramTree'], node: 'Node') -> List[Dict[str, Any]]:

    utilization_rows_dict = {}
    parents_already_met = []
    for tree in program_trees_versions:

        for path, child_node in tree.root_node.descendents.items():

            if child_node == node:
                ff = True
                # link = tree.get_first_link_occurence_using_node(child_node)

                links = tree.get_links_using_node(child_node)
                for link in links:

                    if link.parent not in parents_already_met:
                        parents_already_met.append(link.parent)
                        cmd_parent = command.GetProgramTreesVersionFromNodeCommand(code=link.parent.code,
                                                                                   year=link.parent.year)
                        parent_node_pgm_tree_versions = \
                            search_tree_versions_using_node_service.search_tree_versions_using_node(cmd_parent)
                        if parent_node_pgm_tree_versions is None or parent_node_pgm_tree_versions == []:
                            # Found groups with have no education_group_version
                            cmd = GetProgramTreesFromNodeCommand(code=link.parent.code, year=link.parent.year)
                            parent_node_pgm_tree_versions = search_program_trees_using_node_service.search_program_trees_using_node(cmd)
                        if parent_node_pgm_tree_versions:

                            for parent_tree_version in parent_node_pgm_tree_versions:

                                if isinstance(parent_tree_version, ProgramTreeVersion):
                                    parent_tree = parent_tree_version.get_tree()
                                else:
                                    parent_tree = parent_tree_version

                                for path2, child_node2 in parent_tree.root_node.descendents.items():
                                    if isinstance(child_node2, NodeGroupYear) and child_node2 == link.parent:
                                        gathering = get_explore_parents(parent_tree.get_parents(path2))
                                        lk_to_update = utilization_rows_dict.get(link, [])
                                        if gathering:
                                            lk_to_update.append(gathering)
                                        utilization_rows_dict.update({link: lk_to_update})

                        else:
                            lk_to_update = utilization_rows_dict.get(link, [])
                            if link.parent not in lk_to_update:
                                utilization_rows_dict.update({link: lk_to_update})

    return _buid_utilization_rows(utilization_rows_dict)


def _buid_utilization_rows(utilization_rows_dict: Dict['Node', List['Node']]) -> List[Dict[str, Any]]:
    utilization_rows = []

    for link, training_nodes in utilization_rows_dict.items():
        dd = {}
        for d in training_nodes:
            root_node = d.get('top_node')
            direct_parent = d.get('parent_direct_node')
            if direct_parent:
                key = direct_parent
            else:
                key = root_node
            if key:
                if key not in dd:
                    dd.update({key: []})

                tableau_to_update = dd.get(key)
                if root_node and key != root_node and  root_node not in tableau_to_update:
                    tableau_to_update.append(root_node)
                    dd.update({key: tableau_to_update})

        training_nodes = []
        for k, v in dd.items():
            training_nodes.append({'direct_parent': k, 'top_nodes': v})
        utilization_rows.append(
            {
                'link': link,
                'training_nodes': training_nodes
            }
        )
    return utilization_rows


def get_explore_parents(parents_of_node: List['Node']) -> 'Node':
    if parents_of_node:
        parent_direct_node = None
        top_node = None
        for node in parents_of_node:
            if (node.is_minor_or_deepening()) or (node.is_training() and node.is_finality()):
                parent_direct_node = node
            if node.is_training() or node.is_mini_training():
                top_node = node

        if parent_direct_node is None and top_node is None:
            return None
    return {
        'parent_direct_node': parent_direct_node,
        'top_node': top_node
    }

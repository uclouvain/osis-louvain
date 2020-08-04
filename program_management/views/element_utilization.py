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
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command
from program_management.ddd.service.read import search_tree_versions_using_node_service
from program_management.views.generic import LearningUnitGeneric
from program_management.serializers.node_view import get_program_tree_version_name
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository


class LearningUnitUtilization(PermissionRequiredMixin, LearningUnitGeneric):
    template_name = "learning_unit/tab_utilization.html"

    permission_required = 'base.view_educationgroup'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cmd = command.GetProgramTreesVersionFromNodeCommand(code=self.node.code, year=self.node.year)
        program_trees_versions = search_tree_versions_using_node_service.search_tree_versions_using_node(cmd)

        context['utilization_rows'] = []
        for program_tree_version in program_trees_versions:
            tree = program_tree_version.get_tree()
            for link in tree.get_links_using_node(self.node):
                parent_node_identity = NodeIdentity(code=link.parent.code, year=link.parent.year)
                context['utilization_rows'].append(
                    {'link': link,
                     'link_parent_version_label': get_program_tree_version_name(
                         parent_node_identity,
                         ProgramTreeVersionRepository.search_all_versions_from_root_node(parent_node_identity)
                     ),
                     'root_nodes': [tree.root_node],
                     'root_version_label': "{}".format(
                         program_tree_version.version_label if program_tree_version.version_label else ''
                     )}
                )
        context['utilization_rows'] = sorted(context['utilization_rows'], key=lambda row: row['link'].parent.code)
        return context

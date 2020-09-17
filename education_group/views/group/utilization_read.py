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
from education_group.views.group.common_read import Tab, GroupRead
from program_management.ddd import command
from program_management.ddd.service.read import search_tree_versions_using_node_service
from program_management.serializers.node_view import get_program_tree_version_name
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.views.element_utilization import get_utilization_rows


class GroupReadUtilization(GroupRead):
    template_name = "education_group_app/group/utilization_read.html"
    active_tab = Tab.UTILIZATION

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        node = self.get_object()
        cmd = command.GetProgramTreesVersionFromNodeCommand(code=node.code, year=node.year)
        program_trees_versions = search_tree_versions_using_node_service.search_tree_versions_using_node(cmd)
        trees = []
        for program_tree_version in program_trees_versions:
            trees.append(program_tree_version.get_tree())

        context['utilization_rows'] = get_utilization_rows(trees, node)
        return context

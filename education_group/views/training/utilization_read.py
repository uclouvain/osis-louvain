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
from education_group.views.training.common_read import TrainingRead, Tab
from program_management.ddd.repositories.node import NodeRepository
from program_management.ddd.service.read.search_program_trees_using_node_service import search_program_trees_using_node
from program_management.serializers.program_trees_utilizations import utilizations_serializer


class TrainingReadUtilization(TrainingRead):
    template_name = "education_group_app/training/utilization_read.html"
    active_tab = Tab.UTILIZATION

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'direct_parents': utilizations_serializer(
                self.node_identity,
                search_program_trees_using_node,
                NodeRepository()
            )
        }

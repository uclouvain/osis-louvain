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

import factory.fuzzy

from base.models.enums.education_group_types import GroupType, TrainingType
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class ProgramTreeFinalityDROI2MSIUFactory(ProgramTreeFactory):
    """
    LIURE200S - DROI2MS/IU
        |
        |___ LIURE100T - PARTIEDEBASEDROI2MS/IU
        |
        |___ LIURE101G - LISTEAUCHOIXOPTIONSDROIMS/IU

    """
    root_node = factory.SubFactory(
        NodeGroupYearFactory,
        node_type=TrainingType.MASTER_MS_120,
        code='LIURE200S',
        title='DROI2MS/IU',
    )

    @factory.post_generation
    def generate_children(self, *args, **kwargs):
        end_year = self.root_node.end_year
        current_year = self.root_node.year
        liure100t = NodeGroupYearFactory(
            code='LIURE100T',
            title='PARTIEDEBASEDROI2MS/IU',
            node_type=GroupType.COMMON_CORE,
            end_year=end_year,
            year=current_year,
        )

        liure101g = NodeGroupYearFactory(
            code='LIURE101G',
            title='LISTEAUCHOIXOPTIONSDROIMS/IU',
            node_type=GroupType.OPTION_LIST_CHOICE,
            end_year=end_year,
            year=current_year,
        )

        LinkFactory(
            parent=self.root_node,
            child=liure100t,
        )
        LinkFactory(
            parent=self.root_node,
            child=liure101g,
        )

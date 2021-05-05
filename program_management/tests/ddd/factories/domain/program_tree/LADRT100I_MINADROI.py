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

from base.models.enums.education_group_types import GroupType, MiniTrainingType
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class ProgramTreeMINADROIFactory(ProgramTreeFactory):
    """
    LADRT100I - MINADROI
        |
        |___ LADRT100T - PARTIEDEBASEMINADROI
                  |
                  |___ LADRT102R - MINAUTRESBAC
                          |
                          |___ LDROI1222 (UE)
                          |
                          |___ LDROI1223 (UE)


    """

    root_node = factory.SubFactory(
        NodeGroupYearFactory,
        node_type=MiniTrainingType.ACCESS_MINOR,
        code='LADRT100I',
        title='MINADROI',
    )

    @factory.post_generation
    def generate_children(self, *args, **kwargs):
        ladrt100i = self.root_node
        current_year = self.root_node.year
        end_year = self.root_node.end_year

        ladrt100t = NodeGroupYearFactory(
            code='LADRT100T',
            title='PARTIEDEBASEMINADROI',
            node_type=GroupType.COMMON_CORE,
            end_year=end_year,
            year=current_year,
        )
        ladrt102r = NodeGroupYearFactory(
            code='LADRT102R',
            title='MINAUTRESBAC',
            node_type=GroupType.SUB_GROUP,
            end_year=end_year,
            year=current_year,
        )

        ldroi1222 = NodeLearningUnitYearFactory(code='LDROI1222', year=current_year, end_date=end_year)
        ldroi1223 = NodeLearningUnitYearFactory(code='LDROI1223', year=current_year, end_date=end_year)

        LinkFactory(
            parent=ladrt100i,
            child=ladrt100t
        )
        LinkFactory(
            parent=ladrt100t,
            child=ladrt102r
        )
        LinkFactory(
            parent=ladrt102r,
            child=ldroi1222
        )
        LinkFactory(
            parent=ladrt102r,
            child=ldroi1223
        )

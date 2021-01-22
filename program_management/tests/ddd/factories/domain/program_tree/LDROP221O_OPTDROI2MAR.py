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

from base.models.enums.education_group_types import MiniTrainingType, GroupType
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class ProgramTreeOptionLDROP221OFactory(ProgramTreeFactory):
    """
    LDROP221O - OPTDROI2M/AR
        |
        |___ LDROP100T - PARTIEDEBASE
                |
                |___ LDROP2011 (UE)
                |
                |___ LDROP2012 (UE)
                |
                |___ LDROP2013 (UE)

    """
    root_node = factory.SubFactory(
        NodeGroupYearFactory,
        code='LDROP221O',
        title='OPTDROI2M/AR',
        node_type=MiniTrainingType.OPTION,
    )

    @factory.post_generation
    def generate_children(self, *args, **kwargs):
        end_year = self.root_node.end_year
        current_year = self.root_node.year

        ldrop100t = NodeGroupYearFactory(
            code='LDROP100T',
            title='PARTIEDEBASE',
            node_type=GroupType.COMMON_CORE,
            end_year=end_year,
            year=current_year,
        )

        ldrop2011 = NodeLearningUnitYearFactory(code='LDROP2011', year=current_year, end_date=end_year)
        ldrop2012 = NodeLearningUnitYearFactory(code='LDROP2012', year=current_year, end_date=end_year)
        ldrop2013 = NodeLearningUnitYearFactory(code='LDROP2013', year=current_year, end_date=end_year)
        LinkFactory(
            parent=self.root_node,
            child=ldrop100t,
        )
        LinkFactory(
            parent=ldrop100t,
            child=ldrop2011,
        )
        LinkFactory(
            parent=ldrop100t,
            child=ldrop2012,
        )
        LinkFactory(
            parent=ldrop100t,
            child=ldrop2013,
        )

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
from program_management.tests.ddd.factories.domain.program_tree.LDROP221O_OPTDROI2MAR import \
    ProgramTreeOptionLDROP221OFactory
from program_management.tests.ddd.factories.domain.program_tree.LIURE200S_DROI2MSIU import \
    ProgramTreeFinalityDROI2MSIUFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class ProgramTreeDROI2MFactory(ProgramTreeFactory):
    """
    LDROI200M - DROI2M
        |
        |___ LDROI220T - TCDROI2M
        |        |
        |        |___ LDROI2101 (UE)
        |        |
        |        |___ LDROI2102 (UE)
        |
        |
        |___ LDROI101G - FINALITÉS
        |        |
        |        |___ LIURE200S - DROI2MS/IU
        |                 |
        |                 |___ LIURE100T - PARTIEDEBASEDROI2MS/IU
        |                 |
        |                 |___ LIURE101G - LISTEAUCHOIXOPTIONSDROIMS/IU
        |
        |
        |___ LDROI100G - DROI2MO
                 |
                 |___ LDROP221O - OPTDROI2M/AR
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
        node_type=TrainingType.PGRM_MASTER_120,
        code='LDROI200M',
        title='DROI2M',
    )

    @factory.post_generation
    def generate_children(self, *args, **kwargs):
        ldroi200m = self.root_node
        current_year = self.root_node.year
        end_year = self.root_node.end_year

        ldroi220t = NodeGroupYearFactory(
            code='LDROI220T',
            title='TCDROI2M',
            node_type=GroupType.COMMON_CORE,
            end_year=end_year,
            year=current_year,
        )

        ldroi2101 = NodeLearningUnitYearFactory(code='LDROI2101', year=current_year, end_date=end_year)
        ldroi2102 = NodeLearningUnitYearFactory(code='LDROI2102', year=current_year, end_date=end_year)

        ldroi101g = NodeGroupYearFactory(
            code='LDROI101G',
            title='FINALITÉS',
            node_type=GroupType.FINALITY_120_LIST_CHOICE,
            end_year=end_year,
            year=current_year,
        )

        ldroi100g = NodeGroupYearFactory(
            code='LDROI100G',
            title='DROI2MO',
            node_type=GroupType.OPTION_LIST_CHOICE,
            end_year=end_year,
            year=current_year,
        )

        LinkFactory(
            parent=ldroi200m,
            child=ldroi220t
        )
        LinkFactory(
            parent=ldroi220t,
            child=ldroi2101
        )
        LinkFactory(
            parent=ldroi220t,
            child=ldroi2102
        )
        LinkFactory(
            parent=ldroi200m,
            child=LinkFactory(
                parent=ldroi101g,
                child=ProgramTreeFinalityDROI2MSIUFactory(
                    root_node__year=current_year,
                    root_node__end_year=end_year
                ).root_node
            ).parent
        )
        LinkFactory(
            parent=ldroi200m,
            child=LinkFactory(
                parent=ldroi100g,
                child=ProgramTreeOptionLDROP221OFactory(
                    root_node__year=current_year,
                    root_node__end_year=end_year
                ).root_node
            ).parent
        )

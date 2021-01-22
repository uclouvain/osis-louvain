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
from program_management.tests.ddd.factories.domain.program_tree.LADRT100I_MINADROI import ProgramTreeMINADROIFactory
from program_management.tests.ddd.factories.domain.program_tree.LDROP221O_OPTDROI2MAR import \
    ProgramTreeOptionLDROP221OFactory
from program_management.tests.ddd.factories.domain.program_tree.LIURE200S_DROI2MSIU import \
    ProgramTreeFinalityDROI2MSIUFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class ProgramTreeDROI1BAFactory(ProgramTreeFactory):
    """
    LDROI100B - DROI1BA
        |
        |___ LDROI900T - MATIERECOMMUNE
        |        |
        |        |___ LDRSH900R - SCIENCESHUMAINES
        |                 |
        |                 |___ LDROI1006 (UE)
        |                 |
        |                 |___ LDROI1007 (UE)
        |
        |
        |___ LDROI104G - LISTEAUCHOIXMINEURESDROIBA


    """

    root_node = factory.SubFactory(
        NodeGroupYearFactory,
        node_type=TrainingType.BACHELOR,
        code='LDROI100B',
        title='DROI1BA',
    )

    @factory.post_generation
    def generate_children(self, *args, **kwargs):
        ldroi100b = self.root_node
        current_year = self.root_node.year
        end_year = self.root_node.end_year

        ldroi900t = NodeGroupYearFactory(
            code='LDROI900T',
            title='MATIERECOMMUNE',
            node_type=GroupType.COMMON_CORE,
            end_year=end_year,
            year=current_year,
        )
        ldrsh900r = NodeGroupYearFactory(
            code='LDRSH900R',
            title='SCIENCESHUMAINES',
            node_type=GroupType.SUB_GROUP,
            end_year=end_year,
            year=current_year,
        )

        ldroi104g = NodeGroupYearFactory(
            code='LDROI104G',
            title='LISTEAUCHOIXMINEURESDROIBA',
            node_type=GroupType.MINOR_LIST_CHOICE,
            end_year=end_year,
            year=current_year,
        )

        ldroi1006 = NodeLearningUnitYearFactory(code='LDROI1006', year=current_year, end_date=end_year)
        ldroi1007 = NodeLearningUnitYearFactory(code='LDROI1007', year=current_year, end_date=end_year)

        LinkFactory(
            parent=ldroi100b,
            child=ldroi900t
        )
        LinkFactory(
            parent=ldroi900t,
            child=ldrsh900r
        )
        LinkFactory(
            parent=ldrsh900r,
            child=ldroi1006
        )
        LinkFactory(
            parent=ldrsh900r,
            child=ldroi1007
        )
        LinkFactory(
            parent=ldroi100b,
            child=ldroi104g
        )

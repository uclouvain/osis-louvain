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


class ProgramTreeSPED2MFactory(ProgramTreeFactory):
    """
    LSPED200M - SPED2M
        |
        |___ LSPED200T - TCSPED2M
        |
        |___ LSPED102G - FINALITÉS
        |
        |___ LSPED103G - OPTIONS

    """

    root_node = factory.SubFactory(
        NodeGroupYearFactory,
        node_type=TrainingType.PGRM_MASTER_120,
        code='LSPED200M',
        title='SPED2M',
    )

    @factory.post_generation
    def generate_children(self, *args, **kwargs):
        lsped200m = self.root_node
        current_year = self.root_node.year
        end_year = self.root_node.end_year

        lsped200t = NodeGroupYearFactory(
            code='LSPED200T',
            title='TCSPED2M',
            node_type=GroupType.COMMON_CORE,
            end_year=end_year,
            year=current_year,
        )

        lsped102g = NodeGroupYearFactory(
            code='LSPED102G',
            title='FINALITÉS',
            node_type=GroupType.FINALITY_120_LIST_CHOICE,
            end_year=end_year,
            year=current_year,
        )

        lsped103g = NodeGroupYearFactory(
            code='LSPED103G',
            title='OPTIONS',
            node_type=GroupType.OPTION_LIST_CHOICE,
            end_year=end_year,
            year=current_year,
        )

        LinkFactory(
            parent=lsped200m,
            child=lsped200t
        )
        LinkFactory(
            parent=lsped200m,
            child=lsped102g
        )
        LinkFactory(
            parent=lsped200m,
            child=lsped103g
        )

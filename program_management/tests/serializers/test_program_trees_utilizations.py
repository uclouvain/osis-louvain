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
from unittest.mock import patch

from django.test import SimpleTestCase

from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.repositories.node import NodeRepository
from program_management.serializers.program_trees_utilizations import utilizations_serializer
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory


class TestNodeUtilizationsSerializer2(SimpleTestCase):
    def setUp(self):
        """
        ARKE1BA
        |-----MINMEDI
             |---- LTEMP734R (UE)

        MUSI2M
        |-----MUSI2MS/AR
             |---- LMUSI106T
                  |---- LTEMP734R (UE)

        MUSI1BA
        |-----MINMEDI
             |---- LTEMP734R (UE)

        CLAS1BA
        |-----MINMEDI
             |---- LTEMP734R (UE)
        """
        year = 2020
        self.arke1ba = NodeGroupYearFactory(
            node_id=1, code="LARKE100B", title="ARKE1BA", node_type=TrainingType.BACHELOR, year=year
        )
        self.musi1ba = NodeGroupYearFactory(
            node_id=2, code="LMUSI100B", title="MUSI1BA", node_type=TrainingType.BACHELOR, year=year
        )
        self.clas1ba = NodeGroupYearFactory(
            node_id=3, code="LCLAS100B", title="CLAS1BA", node_type=TrainingType.BACHELOR, year=year
        )
        self.minmedi = NodeGroupYearFactory(
            node_id=4, code="LMEDI100I", title="MINMEDI (mineure)", node_type=MiniTrainingType.OPEN_MINOR, year=year
        )

        self.musi2m = NodeGroupYearFactory(
            node_id=5, code="LMUSI200M", title="MUSI2M", node_type=TrainingType.PGRM_MASTER_120, year=year
        )
        self.musi_2ms_ar = NodeGroupYearFactory(
            node_id=6, code="LMUSI706S", title="MUSI2MS/AR", node_type=TrainingType.MASTER_MS_120, year=year
        )
        self.musi_common_core = NodeGroupYearFactory(
            node_id=7, code="LMUSI106T", title="PARTIEDEBASEMUSI2MS/AR", node_type=GroupType.COMMON_CORE, year=year
        )

        self.ltemp734r = NodeLearningUnitYearFactory(node_id=8, code="LTEMP734R", year=year)

        self.link_arke1ba_minmedi = LinkFactory(parent=self.arke1ba, child=self.minmedi)
        self.link_musi1ba_minmedi = LinkFactory(parent=self.musi1ba, child=self.minmedi)
        self.link_clas1ba_minmedi = LinkFactory(parent=self.clas1ba, child=self.minmedi)
        self.link_minmedi_ltemp734r = LinkFactory(parent=self.minmedi, child=self.ltemp734r)

        self.link_musi2m_musi_2ms = LinkFactory(parent=self.musi2m, child=self.musi_2ms_ar)
        self.link_musi_2ms_musi_common_core = LinkFactory(parent=self.musi_2ms_ar, child=self.musi_common_core)
        self.link_musi_common_core_ltemp734r = LinkFactory(parent=self.musi_common_core, child=self.ltemp734r)

        self.trees_using_node = [
            ProgramTree(root_node=self.musi2m),
            ProgramTree(root_node=self.musi1ba),
            ProgramTree(root_node=self.arke1ba),
            ProgramTree(root_node=self.clas1ba),
        ]

    @patch("program_management.ddd.repositories.node.NodeRepository.get")
    def test_data_are_correctly_formated(self, mock_repository):
        mock_repository.return_value = self.ltemp734r
        result = utilizations_serializer(
            node_identity=self.ltemp734r.entity_id,
            search_program_trees_service=lambda *args: self.trees_using_node,
            node_repository=NodeRepository()
        )
        expected_result = [
            # WARNING : Order is important
            {
                "link": self.link_minmedi_ltemp734r,
                "indirect_parents": [
                    # WARNING : Order is important
                    {
                        "node": self.arke1ba,
                        "indirect_parents": [],
                    },
                    {
                        "node": self.clas1ba,
                        "indirect_parents": [],
                    },
                    {
                        "node": self.musi1ba,
                        "indirect_parents": [],
                    },
                ]
            },
            {
                "link": self.link_musi_common_core_ltemp734r,
                "indirect_parents": [
                    {
                        "node": self.musi_2ms_ar,  # First indirect parent
                        "indirect_parents": [
                            {
                                "node": self.musi2m,  # Indirect parent of indirect parent
                            }
                        ],
                    },
                ]
            }
        ]
        self.assertListEqual(result, expected_result)

#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.domain.program_tree_version.common import ProgramTreeVersionBuilder


class ARKE2MFactory(ProgramTreeVersionBuilder):
    tree_data = {
        "node_type": TrainingType.PGRM_MASTER_120,
        "code": "LARKE200M",
        "title": "ARKE2M",
        "children": [
            {
                "node_type": GroupType.COMMON_CORE,
                "code": "LARKE200T",
                "title": "TRONCOMARKE2M",
                "children": [
                    {
                        "node_type": GroupType.SUB_GROUP,
                        "code": "LARKE912R",
                        "title": "ARKE2M/TCFORMATIONGÉN",
                        "children": [
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "Recherche",
                                "code": "LARKE2892",
                            },
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "Recherche bis",
                                "code": "LARKE2890",
                            }
                        ]
                    }
                ]
            },
            {
                "node_type": GroupType.FINALITY_120_LIST_CHOICE,
                "code": "LARKE105G",
                "title": "FINALITÉSARKE2M",
                "children": [
                    {
                        "node_type": TrainingType.MASTER_MD_120,
                        "code": "ARKE2MD",
                        "title": "LARKE200D",
                        "children": [
                            {
                                "node_type": GroupType.COMMON_CORE,
                                "code": "LARKE102T",
                                "title": "PARTIEDEBASEARKE2MD",
                                "children": []
                            },
                            {
                                "node_type": GroupType.OPTION_LIST_CHOICE,
                                "code": "LARKE108G",
                                "title": "LISTEAUCHOIXOPTIONSARKE2MD",
                                "children": [
                                    {
                                        "node_type": MiniTrainingType.OPTION,
                                        "code": "LARKE203O",
                                        "title": "OPTARKE2M/EP",
                                    },
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "node_type": GroupType.OPTION_LIST_CHOICE,
                "code": "LARKE107G",
                "title": "OPTIONSOUCXARKE2M",
                "children": [
                    {
                        "node_type": MiniTrainingType.OPTION,
                        "code": "LARKE203O",
                        "title": "OPTARKE2M",
                    },
                ]
            },
        ]

    }

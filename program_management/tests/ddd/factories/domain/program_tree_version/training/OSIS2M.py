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


class OSIS2MFactory(ProgramTreeVersionBuilder):
    tree_data = {
        "node_type": TrainingType.PGRM_MASTER_120,
        "code": "LOSIS200M",
        "title": "OSIS2M",
        "children": [
            {
                "node_type": GroupType.COMMON_CORE,
                "code": "LOSIS201T",
                "title": "TRONCCOMMUNOSIS2M",
                "children": [
                    {
                        "node_type": GroupType.SUB_GROUP,
                        "code": "LOSIS201R",
                        "title": "GROUPEMENTA",
                        "children": [
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "UE LINGE",
                                "code": "LINGE2001",
                            },
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "UE LINGE2",
                                "code": "LINGE2002",
                            }
                        ]
                    },
                    {
                        "node_type": NodeType.LEARNING_UNIT,
                        "title": "UE LECGE",
                        "code": "LECGE2004",
                    }
                ]
            },
            {
                "node_type": GroupType.FINALITY_120_LIST_CHOICE,
                "code": "LOSIS104G",
                "title": "LISTEAUCHOIXDEFINALITESOSIS2M",
                "children": [
                    {
                        "node_type": TrainingType.MASTER_MD_120,
                        "code": "LOSIS220D",
                        "title": "OSIS2MD",
                        "children": [
                            {
                                "node_type": GroupType.COMMON_CORE,
                                "code": "LOSIS202T",
                                "title": "PARTIEDEBASEOSIS2MD",
                                "children": [
                                    {
                                        "node_type": GroupType.SUB_GROUP,
                                        "code": "LOSIS210R",
                                        "title": "GROUPEMENTBASE",
                                        "children": [
                                            {
                                                "node_type": NodeType.LEARNING_UNIT,
                                                "title": "UE LSINF",
                                                "code": "LSINF2010",
                                            },
                                        ]
                                    },
                                ]
                            },
                            {
                                "node_type": GroupType.OPTION_LIST_CHOICE,
                                "code": "LOSIS105G",
                                "title": "LISTEAUCHOIXOPTIONSOSIS2MD",
                                "children": [
                                    {
                                        "node_type": MiniTrainingType.OPTION,
                                        "code": "LOSIS200O",
                                        "title": "OPTION2MD/A",
                                    },
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "node_type": GroupType.OPTION_LIST_CHOICE,
                "code": "LOSIS106G",
                "title": "OPTIONSAUCHOIXOSIS2M",
                "children": [
                    {
                        "node_type": MiniTrainingType.OPTION,
                        "code": "LOSIS200O",
                        "title": "OPTION2MD/A",
                    },
                ]
            },
            {
                "node_type": GroupType.COMPLEMENTARY_MODULE,
                "code": "LOSIS111K",
                "title": "OSIS2M1PM",
                "children": [
                    {
                        "node_type": NodeType.LEARNING_UNIT,
                        "title": "UE LBIR",
                        "code": "LBIR1001",
                    },
                    {
                        "node_type": NodeType.LEARNING_UNIT,
                        "code": "LBIR1002",
                        "title": "UE LBIR2",
                    },
                ]
            },
        ]

    }


class OSIS2MSpecificVersionFactory(ProgramTreeVersionBuilder):
    tree_data = {
        "node_type": TrainingType.PGRM_MASTER_120,
        "code": "LOSIS201M",
        "title": "OSIS2M",
        "version_name": "VERSION",
        "children": [
            {
                "node_type": GroupType.COMMON_CORE,
                "code": "LOSIS202T",
                "title": "TRONCCOMMUNOSIS2MV",
                "children": [
                    {
                        "node_type": GroupType.SUB_GROUP,
                        "code": "LOSIS202R",
                        "title": "GROUPEMENTAV",
                        "children": [
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "UE LINGE3",
                                "code": "LINGE2003",
                            }
                        ]
                    }
                ]
            },
            {
                "node_type": GroupType.FINALITY_120_LIST_CHOICE,
                "code": "LOSIS105G",
                "title": "LISTEAUCHOIXDEFINALITESOSIS2MV",
                "children": [
                    {
                        "node_type": TrainingType.MASTER_MD_120,
                        "code": "LOSIS221D",
                        "title": "OSIS2MD",
                        "version_name": "VERSION",
                        "children": [
                            {
                                "node_type": GroupType.COMMON_CORE,
                                "code": "LOSIS203T",
                                "title": "PARTIEDEBASEOSIS2MDV",
                                "children": [
                                    {
                                        "node_type": GroupType.SUB_GROUP,
                                        "code": "LOSIS211R",
                                        "title": "GROUPEMENTBASEV",
                                        "children": [
                                            {
                                                "node_type": NodeType.LEARNING_UNIT,
                                                "title": "UE LSINF1",
                                                "code": "LSINF2011",
                                            },
                                        ]
                                    },
                                ]
                            },
                            {
                                "node_type": GroupType.OPTION_LIST_CHOICE,
                                "code": "LOSIS108G",
                                "title": "LISTEAUCHOIXOPTIONSOSIS2MDV",
                                "children": []
                            }
                        ]
                    }
                ]
            },
            {
                "node_type": GroupType.OPTION_LIST_CHOICE,
                "code": "LOSIS109G",
                "title": "OPTIONSAUCHOIXOSIS2MV",
                "children": []
            }
        ]
    }

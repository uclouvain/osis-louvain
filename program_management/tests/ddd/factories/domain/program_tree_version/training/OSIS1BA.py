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
from base.models.enums.link_type import LinkTypes
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.domain.program_tree_version.common import ProgramTreeVersionBuilder


class OSIS1BAFactory(ProgramTreeVersionBuilder):
    tree_data = {
        "prerequisites": [("LDROI1001", "LSINF1002 OU LSINF1003")],
        "node_type": TrainingType.BACHELOR,
        "code": "LOSIS100B",
        "title": "OSIS1BA",
        "children": [
            {
                "node_type": GroupType.COMMON_CORE,
                "code": "LOSIS101T",
                "title": "TRONCCOMMUNOSIS1BA",
                "children": [
                    {
                        "node_type": GroupType.SUB_GROUP,
                        "code": "LOSIS101R",
                        "title": "GROUPEA",
                        "children": [
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "Info",
                                "code": "LSINF1002",
                            },
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "Base algorithmique",
                                "code": "LSINF1003",
                            }
                        ]
                    },
                    {
                        "node_type": GroupType.SUB_GROUP,
                        "code": "LOSIS102R",
                        "title": "GROUPEB",
                        "children": [
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "Droit des sociétés",
                                "code": "LDROI1001",
                            }
                        ]
                    }
                ]
            },
            {
                "node_type": GroupType.MINOR_LIST_CHOICE,
                "code": "LOSIS101G",
                "title": "LISTEAUCHOIXMINEURESOSIS1BA",
                "children": [
                    {
                        "link_data": {"link_type": LinkTypes.REFERENCE},
                        "node_type": MiniTrainingType.DEEPENING,
                        "code": "LINFO100I",
                        "title": "MININFO",
                        "children": [
                            {
                                "node_type": GroupType.COMMON_CORE,
                                "code": "LINFO100T",
                                "title": "PARTIEDEBASEMININFO",
                                "children": [
                                    {
                                        "node_type": GroupType.SUB_GROUP,
                                        "code": "LINFO101R",
                                        "title": "MINBASEINFO",
                                        "children": [
                                            {
                                                "node_type": NodeType.LEARNING_UNIT,
                                                "title": "Database",
                                                "code": "LINFO1255",
                                            },
                                            {
                                                "node_type": NodeType.LEARNING_UNIT,
                                                "title": "Machine learning",
                                                "code": "LINFO1212",
                                            }
                                        ]
                                    },
                                    {
                                        "node_type": GroupType.SUB_GROUP,
                                        "code": "LINFO102R",
                                        "title": "MINBASEINFO2",
                                        "children": []
                                    }
                                ]
                            }
                        ]
                    },
                ]
            }
        ]
    }

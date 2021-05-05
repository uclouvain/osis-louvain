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

from base.models.enums.education_group_types import GroupType, MiniTrainingType
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.domain.program_tree_version.common import ProgramTreeVersionBuilder


class MINECONFactory(ProgramTreeVersionBuilder):
    tree_data = {
        "node_type": MiniTrainingType.ACCESS_MINOR,
        "code": "LECON100I",
        "title": "MINECON",
        "children": [
            {
                "node_type": GroupType.COMMON_CORE,
                "code": "LECON100T",
                "title": "PARTIEDEBASEMINECON",
                "children": [
                    {
                        "node_type": GroupType.SUB_GROUP,
                        "code": "LECON101R",
                        "title": "MINBASEECO",
                        "children": [
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "Econométrie",
                                "code": "LECON1101",
                            },
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "Economie politique",
                                "code": "LECON1102",
                            }
                        ]
                    }
                ]
            }
        ]
    }


class MINECONSpecificVersionFactory(ProgramTreeVersionBuilder):
    tree_data = {
        "node_type": MiniTrainingType.ACCESS_MINOR,
        "code": "LECON200I",
        "title": "MINECON",
        "version_name": "VERSION",
        "children": [
            {
                "node_type": GroupType.COMMON_CORE,
                "code": "LECON200T",
                "title": "PARTIEDEBASEMINECONV",
                "children": [
                    {
                        "node_type": GroupType.SUB_GROUP,
                        "code": "LECON201R",
                        "title": "MINBASEECOV",
                        "children": [
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "Econométrie plus",
                                "code": "LECON1201",
                            },
                            {
                                "node_type": NodeType.LEARNING_UNIT,
                                "title": "Sciences politiques",
                                "code": "LECON1102",
                            }
                        ]
                    }
                ]
            }
        ]
    }
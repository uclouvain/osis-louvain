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
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipListFactory
from program_management.tests.ddd.factories.domain.prerequisite.prerequisite import PrerequisitesFactory
from program_management.tests.ddd.factories.program_tree import tree_builder


class ProgramTreeBachelorFactory:
    def __new__(cls, current_year: int, end_year: int, *args, **kwargs):
        return cls.produce_bachelor_tree(current_year, end_year)

    @staticmethod
    def produce_bachelor_tree(current_year: int, end_year: int) -> 'ProgramTree':
        tree_data = {
            "node_type": TrainingType.BACHELOR,
            "year": current_year,
            "end_year": end_year,
            "node_id": 1,
            "children": [
                {
                    "node_type": GroupType.COMMON_CORE,
                    "year": current_year,
                    "end_year": end_year,
                    "node_id": 21,
                    "children": [
                        {
                            "node_type": GroupType.SUB_GROUP,
                            "year": current_year,
                            "end_year": end_year,
                            "node_id": 31,
                            "children": [
                                {
                                    "node_type": NodeType.LEARNING_UNIT,
                                    "year": current_year,
                                    "end_date": end_year,
                                    "node_id": 41,
                                },
                                {
                                    "node_type": NodeType.LEARNING_UNIT,
                                    "year": current_year,
                                    "end_date": end_year,
                                    "node_id": 42,
                                }
                            ]
                        }
                    ]
                },
                {
                    "node_type": GroupType.MINOR_LIST_CHOICE,
                    "year": current_year,
                    "end_year": end_year,
                    "node_id": 22,
                    "children": [
                        {
                            "link_data": {"link_type": LinkTypes.REFERENCE},
                            "node_type": MiniTrainingType.DEEPENING,
                            "year": current_year,
                            "end_year": end_year,
                            "node_id": 32,
                            "children": [
                                {
                                    "node_type": GroupType.COMMON_CORE,
                                    "year": current_year,
                                    "end_year": end_year,
                                    "node_id": 1211,
                                    "children": [
                                        {
                                            "node_type": GroupType.SUB_GROUP,
                                            "year": current_year,
                                            "end_year": end_year,
                                            "node_id": 43,
                                            "children": [
                                                {
                                                    "node_type": NodeType.LEARNING_UNIT,
                                                    "year": current_year,
                                                    "end_date": end_year,
                                                    "node_id": 51,
                                                },
                                                {
                                                    "node_type": NodeType.LEARNING_UNIT,
                                                    "year": current_year,
                                                    "end_date": end_year,
                                                    "node_id": 52,
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                    ]
                },
                {
                    "node_type": NodeType.LEARNING_UNIT,
                    "year": current_year,
                    "end_date": end_year,
                }
            ]
        }
        tree = tree_builder(tree_data)
        PrerequisitesFactory.produce_inside_tree(
            tree,
            tree.get_node("1|22|32|1211|43|51"),
            [tree.get_node("1|22|32|1211|43|52")]
        )

        return tree

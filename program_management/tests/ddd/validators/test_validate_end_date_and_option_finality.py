# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################

from django.test import SimpleTestCase

from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from program_management.ddd.validators import _validate_end_date_and_option_finality
from program_management.ddd.validators._end_date_between_finalities_and_masters import \
    CheckEndDateBetweenFinalitiesAndMasters2M
from program_management.tests.ddd.factories.program_tree import tree_builder, ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import StandardProgramTreeVersionFactory
from program_management.tests.ddd.factories.repository.fake import get_fake_program_tree_repository, \
    get_fake_program_tree_version_repository
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestValidateFinalitiesEndDateAndOptions(TestValidatorValidateMixin, SimpleTestCase):
    def setUp(self) -> None:
        tree_data = {
            "node_type": TrainingType.PGRM_MASTER_120,
            "end_year": 2018,
            "children": [
                {
                    "node_type": GroupType.FINALITY_120_LIST_CHOICE,
                    "children": [
                        {
                            "node_type": TrainingType.MASTER_MA_120,
                            "children": [
                                {"node_type": GroupType.OPTION_LIST_CHOICE}
                            ]
                        }
                    ]
                },
                {
                    "node_type": GroupType.OPTION_LIST_CHOICE,
                    "children": [
                        {"node_type": MiniTrainingType.OPTION, "code": "OPTA", "year": 2018},
                        {"node_type": MiniTrainingType.OPTION, "code": "OPTB", "year": 2018}
                    ]
                }
            ]
        }
        self.tree = tree_builder(tree_data)
        self.fake_program_tree_repository = get_fake_program_tree_repository([self.tree])

        self.tree_version = StandardProgramTreeVersionFactory(
            tree=self.tree,
            program_tree_repository=self.fake_program_tree_repository
        )
        self.fake_tree_version_repository = get_fake_program_tree_version_repository([self.tree_version])

        self.finality_option_list_choice = \
            self.tree.root_node.children_as_nodes[0].children_as_nodes[0].children_as_nodes[0]

    def test_should_not_be_valid_when_node_to_attach_is_a_finality_having_an_end_date_greater_than_parent_program(self):
        tree_to_attach_data = {
            "node_type": TrainingType.MASTER_MA_120,
            "end_year": 2019,
        }
        tree_to_attach = tree_builder(tree_to_attach_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_attach)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_attach,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        self.assertValidatorRaises(
            _validate_end_date_and_option_finality.ValidateFinalitiesEndDateAndOptions(
                self.tree.root_node.children_as_nodes[0],
                tree_to_attach.root_node,
                self.fake_program_tree_repository,
            ),
            None
        )

    def test_should_be_invalid_when_node_to_attach_contains_finalities_with_end_date_greater_than_parent_program(self):
        tree_to_attach_data = {
            "node_type": GroupType.FINALITY_120_LIST_CHOICE,
            "children": [
                {"node_type": TrainingType.MASTER_MD_120, "end_year": 2019},
                {"node_type": TrainingType.MASTER_MA_120, "end_year": 2018}
            ]
        }
        tree_to_attach = tree_builder(tree_to_attach_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_attach)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_attach,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        self.assertValidatorRaises(
            _validate_end_date_and_option_finality.ValidateFinalitiesEndDateAndOptions(
                self.tree.root_node.children_as_nodes[0],
                tree_to_attach.root_node,
                self.fake_program_tree_repository,
            ),
            None
        )

    def test_should_not_be_valid_when_node_to_attach_contains_finality_with_undefined_end_year(self):
        tree_to_attach_data = {
            "node_type": GroupType.FINALITY_120_LIST_CHOICE,
            "children": [
                {"node_type": TrainingType.MASTER_MD_120, "end_year": None},
            ]
        }
        tree_to_attach = tree_builder(tree_to_attach_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_attach)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_attach,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        self.assertValidatorRaises(
            _validate_end_date_and_option_finality.ValidateFinalitiesEndDateAndOptions(
                self.tree.root_node.children_as_nodes[0],
                tree_to_attach.root_node,
                self.fake_program_tree_repository,
            ),
            None
        )

    def test_valid_when_node_to_attach_contains_finalities_that_have_lower_or_equal_end_date_to_parent_program(self):
        tree_to_attach_data = {
            "node_type": GroupType.FINALITY_120_LIST_CHOICE,
            "children": [
                {"node_type": TrainingType.MASTER_MD_120, "end_year": 2017},
                {"node_type": TrainingType.MASTER_MA_120, "end_year": 2018}
            ]
        }
        tree_to_attach = tree_builder(tree_to_attach_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_attach)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_attach,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        self.assertValidatorNotRaises(
            _validate_end_date_and_option_finality.ValidateFinalitiesEndDateAndOptions(
                self.tree.root_node.children_as_nodes[0],
                tree_to_attach.root_node,
                self.fake_program_tree_repository,
            )
        )

    def test_invalid_when_node_to_attach_is_an_option_not_contained_in_option_list_of_parent_program(self):
        tree_to_attach_data = {
            "node_type": MiniTrainingType.OPTION,
            "code": "OPTC",
            "year": 2018
        }
        tree_to_attach = tree_builder(tree_to_attach_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_attach)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_attach,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        self.assertValidatorRaises(
            _validate_end_date_and_option_finality.ValidateFinalitiesEndDateAndOptions(
                self.finality_option_list_choice,
                tree_to_attach.root_node,
                self.fake_program_tree_repository,
            ),
            None
        )

    def test_invalid_when_node_to_attach_contains_options_not_contained_in_option_list_of_parent_program(self):
        tree_to_attach_data = {
            "node_type": TrainingType.MASTER_MA_120,
            "end_year": 2017,
            "children": [
                {
                    "node_type": GroupType.OPTION_LIST_CHOICE,
                    "children": [
                        {"node_type": MiniTrainingType.OPTION, "code": "OPTA", "year": 2018},
                        {"node_type": MiniTrainingType.OPTION, "code": "OPTC", "year": 2018}
                    ]
                }
            ]
        }
        tree_to_attach = tree_builder(tree_to_attach_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_attach)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_attach,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        self.assertValidatorRaises(
            _validate_end_date_and_option_finality.ValidateFinalitiesEndDateAndOptions(
                self.finality_option_list_choice,
                tree_to_attach.root_node,
                self.fake_program_tree_repository,
            ),
            None
        )

    def test_valid_when_node_to_attach_contains_options_that_are_also_contained_in_parent_program(self):
        tree_to_attach_data = {
            "node_type": TrainingType.MASTER_MA_120,
            "end_year": 2017,
            "children": [
                {
                    "node_type": GroupType.OPTION_LIST_CHOICE,
                    "children": [
                        {"node_type": MiniTrainingType.OPTION, "code": "OPTA", "year": 2018},
                        {"node_type": MiniTrainingType.OPTION, "code": "OPTB", "year": 2018}
                    ]
                }
            ]
        }
        tree_to_attach = tree_builder(tree_to_attach_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_attach)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_attach,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        self.assertValidatorNotRaises(
            _validate_end_date_and_option_finality.ValidateFinalitiesEndDateAndOptions(
                self.finality_option_list_choice,
                tree_to_attach.root_node,
                self.fake_program_tree_repository,
            ))

    def test_valid_when_attach_option_to_option_list_of_parent_program(self):
        tree_to_attach_data = {"node_type": MiniTrainingType.OPTION, "code": "OPTC", "year": 2018}

        tree_to_attach = tree_builder(tree_to_attach_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_attach)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_attach,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        self.assertValidatorNotRaises(
            _validate_end_date_and_option_finality.ValidateFinalitiesEndDateAndOptions(
                self.tree.root_node.children_as_nodes[1],
                tree_to_attach.root_node,
                self.fake_program_tree_repository,
            )
        )

    def test_should_raise_exception_when_end_year_master_2m_is_inferior_to_one_of_its_finality(self):
        tree_data = {
            "node_type": TrainingType.PGRM_MASTER_120,
            "end_year": 2018,
            "children": [
                {
                    "node_type": GroupType.FINALITY_120_LIST_CHOICE,
                    "children": [
                        {"node_type": TrainingType.MASTER_MA_120, "end_year": 2019},
                        {"node_type": TrainingType.MASTER_MA_120, "end_year": 2018}
                    ]
                }
            ]
        }
        tree = tree_builder(tree_data)
        self.assertValidatorRaises(
            CheckEndDateBetweenFinalitiesAndMasters2M(tree, self.fake_program_tree_repository),
            None
        )

    def test_should_be_valid_when_program_tree_is_not_a_program_2M(self):
        tree_data = {
            "node_type": TrainingType.RESEARCH_CERTIFICATE,
            "end_year": 2018,
            "children": [
                {
                    "node_type": GroupType.FINALITY_120_LIST_CHOICE,
                    "children": [
                        {"node_type": TrainingType.MASTER_MA_120, "end_year": 2019},
                    ]
                }
            ]
        }
        tree = tree_builder(tree_data)
        self.fake_program_tree_repository.root_entities.append(tree)

        self.assertValidatorNotRaises(
            CheckEndDateBetweenFinalitiesAndMasters2M(tree, self.fake_program_tree_repository)
        )

    def test_valid_if_program_has_end_date_greater_or_equal_than_its_finalities(self):
        tree_data = {
            "node_type": TrainingType.PGRM_MASTER_120,
            "end_year": 2019,
            "children": [
                {
                    "node_type": GroupType.FINALITY_120_LIST_CHOICE,
                    "children": [
                        {"node_type": TrainingType.MASTER_MA_120, "end_year": 2019},
                        {"node_type": TrainingType.MASTER_MA_120, "end_year": 2018}
                    ]
                }
            ]
        }
        tree = tree_builder(tree_data)

        self.assertValidatorNotRaises(
            CheckEndDateBetweenFinalitiesAndMasters2M(tree, self.fake_program_tree_repository)
        )

    def test_should_raise_exception_when_finality_end_year_is_superior_to_one_of_its_parent_master(self):
        tree_2m_data = {
            "node_type": TrainingType.PGRM_MASTER_120,
            "end_year": 2018,
            "children": [
                {
                    "node_type": GroupType.FINALITY_120_LIST_CHOICE,
                    "children": [
                        {"node_type": TrainingType.MASTER_MA_120, "end_year": 2019},
                        {"node_type": TrainingType.MASTER_MA_120, "end_year": 2018}
                    ]
                }
            ]
        }
        tree_2m = tree_builder(tree_2m_data)
        self.fake_program_tree_repository.root_entities.append(tree_2m)
        finality_tree = ProgramTreeFactory(root_node=tree_2m.root_node.children_as_nodes[0].children_as_nodes[0])

        self.assertValidatorRaises(
            CheckEndDateBetweenFinalitiesAndMasters2M(finality_tree, self.fake_program_tree_repository),
            None
        )

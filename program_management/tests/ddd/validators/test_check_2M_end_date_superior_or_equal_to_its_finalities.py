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

from base.models.enums.education_group_types import TrainingType, GroupType
from program_management.ddd.validators import _check_finalities_end_date_lower_or_equal_to_2M
from program_management.tests.ddd.factories.program_tree import tree_builder
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestCheck2MEndDateGreaterOrEqualToItsFinalities(SimpleTestCase, TestValidatorValidateMixin):

    def test_should_raise_exception_when_end_year_is_inferior_to_one_of_its_finality(self):
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
        tree_version = ProgramTreeVersionFactory(tree=tree, end_year_of_existence=2018)

        self.assertValidatorRaises(
            _check_finalities_end_date_lower_or_equal_to_2M.Check2MEndDateGreaterOrEqualToItsFinalities(
                tree_version
            ),
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
        tree_version = ProgramTreeVersionFactory(tree=tree, end_year_of_existence=2018)

        self.assertValidatorNotRaises(
            _check_finalities_end_date_lower_or_equal_to_2M.Check2MEndDateGreaterOrEqualToItsFinalities(
                tree_version
            )
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
        tree_version = ProgramTreeVersionFactory(tree=tree, end_year_of_existence=2019)

        self.assertValidatorNotRaises(
            _check_finalities_end_date_lower_or_equal_to_2M.Check2MEndDateGreaterOrEqualToItsFinalities(
                tree_version
            )
        )

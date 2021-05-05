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
import attr

from education_group.ddd.domain.exception import CreditShouldBeGreaterOrEqualsThanZero, ContentConstraintTypeMissing
from program_management.ddd.command import UpdateTrainingVersionCommand
from program_management.ddd.domain.exception import CannotDeleteSpecificVersionDueToTransitionVersionEndDate, \
    Program2MEndDateLowerThanItsFinalitiesException, FinalitiesEndDateGreaterThanTheirMasters2MException, \
    CannotExtendTransitionDueToExistenceOfOtherTransitionException
from program_management.ddd.service.write import update_and_postpone_training_version_service
from program_management.tests.ddd.factories.domain.program_tree_version.training.OSIS2M import OSIS2MFactory, \
    OSIS2MSpecificVersionFactory
from testing.testcases import DDDTestCase


class TestUpdateTrainingVersion(DDDTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.osis2m_standard_version = OSIS2MFactory()[0]
        self.osis2m_specific_version = OSIS2MSpecificVersionFactory()[0]

        self.cmd = UpdateTrainingVersionCommand(
            offer_acronym=self.osis2m_specific_version.entity_id.offer_acronym,
            version_name=self.osis2m_specific_version.version_name,
            transition_name=self.osis2m_specific_version.transition_name,
            year=self.osis2m_specific_version.entity_id.year,
            credits=23,
            end_year=None,
            title_fr="Bachelier en info",
            title_en="Bachelor info",
            teaching_campus_name="LLN",
            management_entity_acronym="INFO",
            teaching_campus_organization_name='UCL',
            constraint_type=None,
            min_constraint=None,
            max_constraint=None,
            remark_fr=None,
            remark_en=None,
        )

    def test_credits_must_be_greater_than_0(self):
        cmd = attr.evolve(self.cmd, credits=-1)

        with self.assertRaisesBusinessException(CreditShouldBeGreaterOrEqualsThanZero):
            update_and_postpone_training_version_service.update_and_postpone_training_version(cmd)

    def test_constraints_must_be_legit(self):
        cmd = attr.evolve(self.cmd, min_constraint=150)

        with self.assertRaisesBusinessException(ContentConstraintTypeMissing):
            update_and_postpone_training_version_service.update_and_postpone_training_version(cmd)

    def test_cannot_reduce_end_year_of_program_2m_to_one_shorter_to_its_finalities(self):
        cmd = attr.evolve(self.cmd, end_year=self.cmd.year)

        with self.assertRaisesBusinessException(Program2MEndDateLowerThanItsFinalitiesException):
            update_and_postpone_training_version_service.update_and_postpone_training_version(cmd)

    def test_cannot_increase_end_year_of_finality_to_one_greater_than_its_program(self):
        cmd = attr.evolve(
            self.cmd,
            offer_acronym="OSIS2MD",
            end_year=self.osis2m_specific_version.end_year_of_existence + 1
        )

        with self.assertRaisesBusinessException(FinalitiesEndDateGreaterThanTheirMasters2MException):
            update_and_postpone_training_version_service.update_and_postpone_training_version(cmd)

    def test_cannot_increase_transition_end_date_to_a_year_where_a_transition_already_exists(self):
        transition_in_future = OSIS2MSpecificVersionFactory.create_transition_from_tree_version(
            self.osis2m_specific_version,
            from_start_year=2022,
            transition_name="TRANSITION FUTURE"
        )[0]
        transition_in_past = OSIS2MSpecificVersionFactory.create_transition_from_tree_version(
            self.osis2m_specific_version,
            end_year=2021
        )[0]
        cmd = attr.evolve(
            self.cmd,
            transition_name=transition_in_past.transition_name,
            end_year=self.osis2m_specific_version.end_year_of_existence
        )

        with self.assertRaisesBusinessException(CannotExtendTransitionDueToExistenceOfOtherTransitionException):
            update_and_postpone_training_version_service.update_and_postpone_training_version(cmd)

    def test_cannot_reduce_specific_version_date_to_one_lower_than_its_transition(self):
        cmd_increase_specific_version_end_date = attr.evolve(
            self.cmd,
            end_year=self.osis2m_specific_version.end_year_of_existence + 1
        )
        update_and_postpone_training_version_service.update_and_postpone_training_version(
            cmd_increase_specific_version_end_date
        )

        OSIS2MSpecificVersionFactory.create_transition_from_tree_version(
            self.osis2m_specific_version,
        )

        cmd = attr.evolve(
            self.cmd,
            end_year=self.osis2m_specific_version.end_year_of_existence - 2
        )
        with self.assertRaisesBusinessException(CannotDeleteSpecificVersionDueToTransitionVersionEndDate):
            update_and_postpone_training_version_service.update_and_postpone_training_version(cmd)

    def test_should_return_program_tree_version_identity(self):
        result = update_and_postpone_training_version_service.update_and_postpone_training_version(self.cmd)

        expected = [
            attr.evolve(self.osis2m_specific_version.entity_id, year=year)
            for year in range(self.cmd.year, 2027)
        ]

        self.assertEqual(expected, result)

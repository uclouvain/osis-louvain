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

from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import MiniTrainingType
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd import command
from education_group.ddd.domain.exception import CodeAlreadyExistException, AcronymRequired, AcronymAlreadyExist, \
    StartYearGreaterThanEndYearException, CreditShouldBeGreaterOrEqualsThanZero, ContentConstraintTypeMissing
from education_group.ddd.domain.mini_training import MiniTrainingIdentity
from education_group.tests.ddd.factories.group import GroupFactory
from program_management.ddd.command import GetProgramTreeVersionCommand
from program_management.ddd.domain.program_tree_version import STANDARD, NOT_A_TRANSITION
from program_management.ddd.domain.service.calculate_end_postponement import DEFAULT_YEARS_TO_POSTPONE
from program_management.ddd.service.read import get_program_tree_version_service
from program_management.ddd.service.write import create_mini_training_with_program_tree
from testing.testcases import DDDTestCase


class TestCreateAndReportMiniTrainingWithProgramTree(DDDTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.max_postponement_year = cls.starting_academic_year_year + DEFAULT_YEARS_TO_POSTPONE

    def setUp(self) -> None:
        super().setUp()

        self.cmd = command.CreateMiniTrainingCommand(
            code="LMINI200I",
            year=2021,
            type=MiniTrainingType.OPTION.name,
            abbreviated_title="MININFO",
            title_fr="Mineure en info",
            title_en="Minor info",
            keywords="",
            status=ActiveStatusEnum.ACTIVE.name,
            schedule_type=ScheduleTypeEnum.DAILY.name,
            credits=20,
            constraint_type=ConstraintTypeEnum.CREDITS.name,
            min_constraint=0,
            max_constraint=5,
            management_entity_acronym="INFO",
            teaching_campus_name="LLN",
            organization_name="UCL",
            remark_fr="",
            remark_en="",
            start_year=2021,
            end_year=None
        )

    def test_cannot_create_mini_training_for_which_code_already_exists(self):
        GroupFactory(entity_identity__code=self.cmd.code, persist=True)

        with self.assertRaisesBusinessException(CodeAlreadyExistException):
            create_mini_training_with_program_tree.create_and_report_mini_training_with_program_tree(self.cmd)

    def test_acronym_should_be_required(self):
        cmd = attr.evolve(self.cmd, abbreviated_title="")
        with self.assertRaisesBusinessException(AcronymRequired):
            create_mini_training_with_program_tree.create_and_report_mini_training_with_program_tree(cmd)

    def test_cannot_create_mini_training_for_which_acronym_already_exists(self):
        GroupFactory(abbreviated_title=self.cmd.abbreviated_title, persist=True)

        with self.assertRaisesBusinessException(AcronymAlreadyExist):
            create_mini_training_with_program_tree.create_and_report_mini_training_with_program_tree(self.cmd)

    def test_start_year_cannot_be_greater_than_end_year(self):
        cmd = attr.evolve(self.cmd, end_year=self.cmd.start_year - 1)

        with self.assertRaisesBusinessException(StartYearGreaterThanEndYearException):
            create_mini_training_with_program_tree.create_and_report_mini_training_with_program_tree(cmd)

    def test_credits_cannot_be_inferior_to_0(self):
        cmd = attr.evolve(self.cmd, credits=-1)

        with self.assertRaisesBusinessException(CreditShouldBeGreaterOrEqualsThanZero):
            create_mini_training_with_program_tree.create_and_report_mini_training_with_program_tree(cmd)

    def test_if_min_or_max_constraint_is_set_then_constraint_type_must_be_set(self):
        # For all business rules for constraints see
        # education_group.tests.ddd.service.write.test_create_group_service.TestCreateGroup
        cmd = attr.evolve(self.cmd, constraint_type=None)

        with self.assertRaisesBusinessException(ContentConstraintTypeMissing):
            create_mini_training_with_program_tree.create_and_report_mini_training_with_program_tree(cmd)

    def test_should_return_identities_of_mini_training_created(self):
        result = create_mini_training_with_program_tree.create_and_report_mini_training_with_program_tree(self.cmd)

        expected = [
            MiniTrainingIdentity(acronym=self.cmd.abbreviated_title, year=year)
            for year in range(2021, self.max_postponement_year+1)
        ]
        self.assertListEqual(expected, result)

    def test_should_create_mini_trainings_until_end_year_when_inferior_to_max_postponement_year(self):
        cmd = attr.evolve(self.cmd, end_year=self.cmd.start_year + 2)

        result = create_mini_training_with_program_tree.create_and_report_mini_training_with_program_tree(cmd)

        expected = [
            MiniTrainingIdentity(acronym=self.cmd.abbreviated_title, year=year)
            for year in range(cmd.start_year, cmd.end_year + 1)
        ]
        self.assertListEqual(expected, result)

    def test_should_create_tree_versions_of_mini_trainings(self):
        mini_training_identities = create_mini_training_with_program_tree.\
            create_and_report_mini_training_with_program_tree(self.cmd)

        cmds = [
            GetProgramTreeVersionCommand(
                acronym=identity.acronym,
                year=identity.year,
                version_name=STANDARD,
                transition_name=NOT_A_TRANSITION
            )
            for identity in mini_training_identities
        ]

        tree_versions = [get_program_tree_version_service.get_program_tree_version(cmd) for cmd in cmds]
        self.assertEqual(len(mini_training_identities), len(tree_versions))

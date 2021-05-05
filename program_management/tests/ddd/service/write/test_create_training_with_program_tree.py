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
import random

import attr

from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd import command
from education_group.ddd.domain.exception import CodeAlreadyExistException, AcronymRequired, AcronymAlreadyExist, \
    StartYearGreaterThanEndYearException, HopsFieldsAllOrNone, \
    CreditShouldBeGreaterOrEqualsThanZero, ContentConstraintTypeMissing, \
    AresCodeShouldBeGreaterOrEqualsThanZeroAndLessThan9999, AresGracaShouldBeGreaterOrEqualsThanZeroAndLessThan9999, \
    AresAuthorizationShouldBeGreaterOrEqualsThanZeroAndLessThan9999
from education_group.ddd.domain.training import TrainingIdentity
from education_group.ddd.validators._hops_validator import TRAINING_TYPES_FOR_WHICH_ARES_GRACA_IS_OPTIONAL
from education_group.tests.ddd.factories.group import GroupFactory
from program_management.ddd.command import GetProgramTreeVersionCommand
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION, STANDARD
from program_management.ddd.domain.service.calculate_end_postponement import DEFAULT_YEARS_TO_POSTPONE
from program_management.ddd.service.read import get_program_tree_version_service
from program_management.ddd.service.write import create_training_with_program_tree
from testing.testcases import DDDTestCase


class TestCreateAndReportTrainingWithProgramTree(DDDTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.max_postponement_year = cls.starting_academic_year_year + DEFAULT_YEARS_TO_POSTPONE

    def setUp(self) -> None:
        super().setUp()

        self.cmd = command.CreateAndPostponeTrainingAndProgramTreeCommand(
            code="INFO1BA",
            year=2021,
            type=TrainingType.BACHELOR.name,
            abbreviated_title="INFO100B",
            title_fr="Bachelier en info",
            title_en="Bachelor info",
            keywords="",
            status=ActiveStatusEnum.ACTIVE.name,
            schedule_type=ScheduleTypeEnum.DAILY.name,
            credits=180,
            constraint_type=ConstraintTypeEnum.CREDITS.name,
            min_constraint=0,
            max_constraint=5,
            remark_fr="",
            remark_en="",
            start_year=2021,
            end_year=None,
            duration=3,
            partial_title_fr=None,
            partial_title_en=None,
            internship_presence=None,
            is_enrollment_enabled=False,
            has_online_re_registration=False,
            has_partial_deliberation=False,
            has_admission_exam=False,
            has_dissertation=False,
            produce_university_certificate=True,
            decree_category=None,
            rate_code=None,
            main_language='French',
            english_activities=None,
            other_language_activities=None,
            internal_comment="",
            main_domain_code=None,
            main_domain_decree=None,
            secondary_domains=[],
            isced_domain_code=None,
            management_entity_acronym="INFO",
            administration_entity_acronym="INFO",
            teaching_campus_name="LLN",
            teaching_campus_organization_name='UCL',
            enrollment_campus_name="LLN",
            enrollment_campus_organization_name="UCL",
            other_campus_activities=None,
            funding_orientation=None,
            can_be_international_funded=True,
            international_funding_orientation=None,
            ares_code=10,
            ares_graca=25,
            ares_authorization=15,
            code_inter_cfb=None,
            coefficient=None,
            academic_type=None,
            duration_unit=None,
            leads_to_diploma=True,
            printing_title='',
            professional_title='',
            can_be_funded=True,
        )

    def test_cannot_create_training_for_which_code_already_exists(self):
        GroupFactory(entity_identity__code=self.cmd.code, persist=True)

        with self.assertRaisesBusinessException(CodeAlreadyExistException):
            create_training_with_program_tree.create_and_report_training_with_program_tree(self.cmd)

    def test_acronym_should_be_required(self):
        cmd = attr.evolve(self.cmd, abbreviated_title="")
        with self.assertRaisesBusinessException(AcronymRequired):
            create_training_with_program_tree.create_and_report_training_with_program_tree(cmd)

    def test_cannot_create_training_for_which_acronym_already_exists(self):
        GroupFactory(abbreviated_title=self.cmd.abbreviated_title, persist=True)

        with self.assertRaisesBusinessException(AcronymAlreadyExist):
            create_training_with_program_tree.create_and_report_training_with_program_tree(self.cmd)

    def test_start_year_cannot_be_greater_than_end_year(self):
        cmd = attr.evolve(self.cmd, end_year=self.cmd.start_year - 1)

        with self.assertRaisesBusinessException(StartYearGreaterThanEndYearException):
            create_training_with_program_tree.create_and_report_training_with_program_tree(cmd)

    def test_credits_cannot_be_inferior_to_0(self):
        cmd = attr.evolve(self.cmd, credits=-1)

        with self.assertRaisesBusinessException(CreditShouldBeGreaterOrEqualsThanZero):
            create_training_with_program_tree.create_and_report_training_with_program_tree(cmd)

    def test_if_min_or_max_constraint_is_set_then_constraint_type_must_be_set(self):
        # For all business rules for constraints see
        # education_group.tests.ddd.service.write.test_create_group_service.TestCreateGroup
        cmd = attr.evolve(self.cmd, constraint_type=None)

        with self.assertRaisesBusinessException(ContentConstraintTypeMissing):
            create_training_with_program_tree.create_and_report_training_with_program_tree(cmd)

    def test_hops_valus_can_all_be_none(self):
        cmd = attr.evolve(
            self.cmd,
            ares_code=None,
            ares_graca=None,
            ares_authorization=None
        )

        result = create_training_with_program_tree.create_and_report_training_with_program_tree(cmd)
        self.assertTrue(result)

    def test_hops_values_should_all_be_defined(self):
        cmd = attr.evolve(
            self.cmd,
            ares_code=10,
            ares_graca=None,
            ares_authorization=10
        )

        with self.assertRaisesBusinessException(HopsFieldsAllOrNone):
            create_training_with_program_tree.create_and_report_training_with_program_tree(cmd)

    def test_ares_graca_is_optional_for_formation_phd_and_certificates_and_capaes(self):
        cmd = attr.evolve(
            self.cmd,
            type=random.choice(TRAINING_TYPES_FOR_WHICH_ARES_GRACA_IS_OPTIONAL),
            ares_code=10,
            ares_graca=None,
            ares_authorization=10
        )

        result = create_training_with_program_tree.create_and_report_training_with_program_tree(cmd)
        self.assertTrue(result)

    def test_hops_values_should_be_comprised_between_0_and_9999(self):
        cmds_with_expected_exception = [
            (attr.evolve(self.cmd, ares_code=-1, ares_graca=52, ares_authorization=21),
             AresCodeShouldBeGreaterOrEqualsThanZeroAndLessThan9999),
            (attr.evolve(self.cmd, ares_code=1, ares_graca=-1, ares_authorization=21),
             AresGracaShouldBeGreaterOrEqualsThanZeroAndLessThan9999),
            (attr.evolve(self.cmd, ares_code=1, ares_graca=52, ares_authorization=-1),
             AresAuthorizationShouldBeGreaterOrEqualsThanZeroAndLessThan9999)
        ]
        for cmd, exception in cmds_with_expected_exception:
            with self.subTest(cmd=cmd):
                with self.assertRaisesBusinessException(exception):
                    create_training_with_program_tree.create_and_report_training_with_program_tree(cmd)

    def test_should_return_identities_of_trainings_created(self):
        result = create_training_with_program_tree.create_and_report_training_with_program_tree(self.cmd)

        expected = [
            TrainingIdentity(acronym=self.cmd.abbreviated_title, year=year)
            for year in range(2021, self.max_postponement_year+1)
        ]
        self.assertListEqual(expected, result)

    def test_should_create_trainings_until_end_year_when_inferior_to_max_postponement_year(self):
        cmd = attr.evolve(self.cmd, end_year=self.cmd.start_year + 2)

        result = create_training_with_program_tree.create_and_report_training_with_program_tree(cmd)

        expected = [
            TrainingIdentity(acronym=self.cmd.abbreviated_title, year=year)
            for year in range(cmd.start_year, cmd.end_year + 1)
        ]
        self.assertListEqual(expected, result)

    def test_should_create_tree_versions_of_trainings(self):
        training_identities = create_training_with_program_tree. \
            create_and_report_training_with_program_tree(self.cmd)

        cmds = [
            GetProgramTreeVersionCommand(
                acronym=identity.acronym,
                year=identity.year,
                version_name=STANDARD,
                transition_name=NOT_A_TRANSITION
            )
            for identity in training_identities
        ]

        tree_versions = [get_program_tree_version_service.get_program_tree_version(cmd) for cmd in cmds]
        self.assertEqual(len(training_identities), len(tree_versions))

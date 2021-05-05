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
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd.command import GetTrainingCommand
from education_group.ddd.domain.exception import CreditShouldBeGreaterOrEqualsThanZero, ContentConstraintTypeMissing, \
    HopsFieldsAllOrNone
from education_group.ddd.service.read import get_training_service
from program_management.ddd.command import PostponeTrainingAndRootGroupModificationWithProgramTreeCommand
from program_management.ddd.domain.exception import Program2MEndDateLowerThanItsFinalitiesException, \
    FinalitiesEndDateGreaterThanTheirMasters2MException
from program_management.ddd.service.write import postpone_training_and_program_tree_modifications_service
from program_management.tests.ddd.factories.domain.program_tree_version.training.OSIS2M import OSIS2MFactory
from testing.testcases import DDDTestCase


class TestPostponeTrainingAndProgramTreeModificationsService(DDDTestCase):
    def setUp(self):
        super().setUp()

        self.osis2m = OSIS2MFactory()[0]
        self.osis2m_training = get_training_service.get_training(
            GetTrainingCommand(acronym=self.osis2m.entity_id.offer_acronym, year=self.osis2m.entity_id.year)
        )

        self.cmd = PostponeTrainingAndRootGroupModificationWithProgramTreeCommand(
            postpone_from_acronym=self.osis2m.entity_id.offer_acronym,
            postpone_from_year=self.osis2m.entity_id.year,
            status=ActiveStatusEnum.ACTIVE.name,
            code=self.osis2m.program_tree_identity.code,
            credits=23,
            duration=3,
            title_fr=self.osis2m_training.titles.title_fr,
            title_en=self.osis2m_training.titles.title_en,
            partial_title_fr="",
            partial_title_en="",
            keywords="hello world",
            internship_presence=self.osis2m_training.internship_presence.name,
            is_enrollment_enabled=self.osis2m_training.is_enrollment_enabled,
            has_online_re_registration=self.osis2m_training.has_online_re_registration,
            has_partial_deliberation=self.osis2m_training.has_partial_deliberation,
            has_admission_exam=self.osis2m_training.has_admission_exam,
            has_dissertation=self.osis2m_training.has_dissertation,
            produce_university_certificate=self.osis2m_training.produce_university_certificate,
            main_language=self.osis2m_training.main_language,
            english_activities=False,
            other_language_activities=False,
            internal_comment=self.osis2m_training.internal_comment,
            main_domain_code=self.osis2m_training.main_domain.code,
            main_domain_decree=self.osis2m_training.main_domain.decree_name,
            secondary_domains=[],
            isced_domain_code=self.osis2m_training.isced_domain.code,
            management_entity_acronym="OSIS",
            administration_entity_acronym="OSIS",
            end_year=self.osis2m.end_year_of_existence,
            teaching_campus_name="OSIS",
            teaching_campus_organization_name="OSIS",
            enrollment_campus_name="OSIS",
            enrollment_campus_organization_name="OSIS",
            other_campus_activities=self.osis2m_training.other_campus_activities.name,
            funding_orientation=self.osis2m_training.funding.funding_orientation.name,
            can_be_international_funded=self.osis2m_training.funding.can_be_international_funded,
            international_funding_orientation=self.osis2m_training.funding.international_funding_orientation.name,
            ares_code=None,
            ares_graca=None,
            ares_authorization=None,
            code_inter_cfb=None,
            coefficient=None,
            duration_unit=None,
            leads_to_diploma=None,
            printing_title=None,
            professional_title=None,
            constraint_type=None,
            min_constraint=None,
            max_constraint=None,
            remark_fr=None,
            remark_en=None,
            can_be_funded=None,
            organization_name="ORG",
            schedule_type=ScheduleTypeEnum.DAILY.name,
            decree_category=self.osis2m_training.decree_category.name,
            rate_code=None,
        )

    def test_credits_must_be_greater_than_0(self):
        cmd = attr.evolve(self.cmd, credits=-1)

        with self.assertRaisesBusinessException(CreditShouldBeGreaterOrEqualsThanZero):
            postpone_training_and_program_tree_modifications_service.postpone_training_and_program_tree_modifications(
                cmd
            )

    def test_constraints_must_be_legit(self):
        cmd = attr.evolve(self.cmd, min_constraint=150)

        with self.assertRaisesBusinessException(ContentConstraintTypeMissing):
            postpone_training_and_program_tree_modifications_service.postpone_training_and_program_tree_modifications(
                cmd
            )

    def test_hops_value_should_be_legit(self):
        cmd = attr.evolve(self.cmd, ares_code=10)

        with self.assertRaisesBusinessException(HopsFieldsAllOrNone):
            postpone_training_and_program_tree_modifications_service.postpone_training_and_program_tree_modifications(
                cmd
            )

    def test_cannot_reduce_end_year_of_program_2m_to_one_shorter_to_its_finalities(self):
        cmd = attr.evolve(self.cmd, end_year=self.cmd.postpone_from_year)

        with self.assertRaisesBusinessException(Program2MEndDateLowerThanItsFinalitiesException):
            postpone_training_and_program_tree_modifications_service.postpone_training_and_program_tree_modifications(
                cmd
            )

    def test_cannot_increase_end_year_of_finality_to_one_greater_than_its_program(self):
        cmd = attr.evolve(
            self.cmd,
            postpone_from_acronym="OSIS2MD",
            end_year=self.osis2m.end_year_of_existence + 1
        )

        with self.assertRaisesBusinessException(FinalitiesEndDateGreaterThanTheirMasters2MException):
            postpone_training_and_program_tree_modifications_service.postpone_training_and_program_tree_modifications(
                cmd
            )

    def test_should_return_training_identities(self):
        result = postpone_training_and_program_tree_modifications_service.\
            postpone_training_and_program_tree_modifications(
                self.cmd
            )

        expected = [
            attr.evolve(self.osis2m_training.entity_id, year=year)
            for year in range(self.cmd.postpone_from_year, 2026)
        ]
        self.assertListEqual(expected, result)

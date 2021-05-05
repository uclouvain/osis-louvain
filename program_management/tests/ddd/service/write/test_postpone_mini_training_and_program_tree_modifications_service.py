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

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd.command import GetMiniTrainingCommand
from education_group.ddd.service.read import get_mini_training_service
from program_management.ddd.command import PostponeMiniTrainingAndRootGroupModificationWithProgramTreeCommand
from program_management.ddd.service.write import postpone_mini_training_and_program_tree_modifications_service
from program_management.tests.ddd.factories.domain.program_tree_version.mini_training.MINECON import MINECONFactory
from testing.testcases import DDDTestCase


class TestPostponeMiniTrainingAndProgramTreeModificationsService(DDDTestCase):
    def setUp(self):
        super().setUp()

        self.minecon = MINECONFactory()[0]
        self.minecon_mini_training = get_mini_training_service.get_mini_training(
            GetMiniTrainingCommand(acronym=self.minecon.entity_id.offer_acronym, year=self.minecon.entity_id.year)
        )

        self.cmd = PostponeMiniTrainingAndRootGroupModificationWithProgramTreeCommand(
            abbreviated_title=self.minecon.entity_id.offer_acronym,
            year=self.minecon.entity_id.year,
            status=ActiveStatusEnum.ACTIVE.name,
            code=self.minecon.program_tree_identity.code,
            credits=23,
            title_fr=self.minecon_mini_training.titles.title_fr,
            title_en=self.minecon_mini_training.titles.title_en,
            keywords="hello world",
            management_entity_acronym="OSIS",
            end_year=self.minecon.end_year_of_existence,
            teaching_campus_name="OSIS",
            teaching_campus_organization_name="OSIS",
            constraint_type=None,
            min_constraint=None,
            max_constraint=None,
            remark_fr=None,
            remark_en=None,
            organization_name="ORG",
            schedule_type=ScheduleTypeEnum.DAILY.name,
        )

    def test_credits_must_be_greater_than_0(self):
        cmd = attr.evolve(self.cmd, credits=-1)

        with self.assertRaises(MultipleBusinessExceptions):
            postpone_mini_training_and_program_tree_modifications_service.\
                postpone_mini_training_and_program_tree_modifications(
                    cmd
                )

    def test_constraints_must_be_legit(self):
        cmd = attr.evolve(self.cmd, min_constraint=150)

        with self.assertRaises(MultipleBusinessExceptions):
            postpone_mini_training_and_program_tree_modifications_service. \
                postpone_mini_training_and_program_tree_modifications(
                    cmd
                )

    def test_should_return_mini_training_identities(self):
        result = postpone_mini_training_and_program_tree_modifications_service. \
            postpone_mini_training_and_program_tree_modifications(
                self.cmd
            )

        expected = [
            attr.evolve(self.minecon_mini_training.entity_id, year=year)
            for year in range(self.cmd.year, 2026)
        ]
        self.assertListEqual(expected, result)

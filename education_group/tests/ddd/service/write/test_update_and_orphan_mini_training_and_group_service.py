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
from mock import patch

from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd import command
from education_group.ddd.domain import mini_training
from education_group.ddd.service.write import update_mini_training_and_group_service
from education_group.tests.factories.mini_training import MiniTrainingFactory
from testing.testcases import DDDTestCase


@patch("education_group.ddd.service.write.update_group_service.update_group")
class TestUpdateAndPostponeMiniTrainingAndGroupService(DDDTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = command.UpdateMiniTrainingAndGroupCommand(
            year=2018,
            code="LTRONC1",
            abbreviated_title="OPT",
            title_fr="Tronc commun",
            title_en="Common core",
            credits=20,
            constraint_type=ConstraintTypeEnum.CREDITS.name,
            min_constraint=0,
            max_constraint=10,
            management_entity_acronym="DRT",
            teaching_campus_name="Mons Fucam",
            organization_name="UCLouvain",
            remark_fr="Remarque en français",
            remark_en="Remarque en anglais",
            end_year=None,
            keywords="A key",
            schedule_type=ScheduleTypeEnum.DAILY.name,
            status=ActiveStatusEnum.ACTIVE.name,
        )

    def setUp(self) -> None:
        super().setUp()
        self.mini_training_2018 = MiniTrainingFactory(
            entity_identity__acronym=self.cmd.abbreviated_title,
            entity_identity__year=2018,
            persist=True
        )
        self.mini_training_2019 = MiniTrainingFactory(
            entity_identity__acronym=self.cmd.abbreviated_title,
            entity_identity__year=2019,
            persist=True
        )

    def test_should_return_entity_id_of_updated_mini_trainings(self, mock_update_group):
        result = update_mini_training_and_group_service.update_mini_training_and_group(self.cmd)
        self.assertEqual(self.mini_training_2018.entity_id, result)

    def test_should_update_value_of_mini_trainings_based_on_command_value(self, mock_update_group):
        entity_id = update_mini_training_and_group_service.update_mini_training_and_group(self.cmd)

        mini_training_update = self.fake_mini_training_repository.get(entity_id)
        self.assert_has_same_value_as_update_command(mini_training_update)

    def assert_has_same_value_as_update_command(self, update_mini_training: 'mini_training.MiniTraining'):
        self.assertEqual(update_mini_training.credits, self.cmd.credits)
        self.assertEqual(update_mini_training.titles.title_fr, self.cmd.title_fr)
        self.assertEqual(update_mini_training.titles.title_en, self.cmd.title_en)
        self.assertEqual(update_mini_training.status.name, self.cmd.status)
        self.assertEqual(update_mini_training.keywords, self.cmd.keywords)
        self.assertEqual(update_mini_training.management_entity.acronym, self.cmd.management_entity_acronym)
        self.assertEqual(update_mini_training.end_year, self.cmd.end_year)
        self.assertEqual(update_mini_training.schedule_type.name, self.cmd.schedule_type)

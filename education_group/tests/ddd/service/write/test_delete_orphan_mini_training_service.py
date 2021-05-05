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

from education_group.ddd import command
from education_group.ddd.domain import exception
from education_group.ddd.service.write import delete_orphan_mini_training_service
from education_group.tests.factories.mini_training import MiniTrainingFactory
from testing.testcases import DDDTestCase


class TestDeleteOrphanMiniTraining(DDDTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = command.DeleteOrphanMiniTrainingCommand(
            year=2018,
            abbreviated_title="MAP29"
        )

    def setUp(self) -> None:
        super().setUp()
        self.mini_training_2018 = MiniTrainingFactory(
            entity_identity__acronym=self.cmd.abbreviated_title,
            entity_identity__year=self.cmd.year,
            persist=True
        )

    def test_should_return_entity_identity_of_deleted_mini_training(self):
        result = delete_orphan_mini_training_service.delete_orphan_mini_training(self.cmd)

        expected_result = self.mini_training_2018.entity_id
        self.assertEqual(expected_result, result)

    def test_should_remove_mini_training_from_repository(self):
        entity_identity_of_deleted_mini_training = delete_orphan_mini_training_service.delete_orphan_mini_training(
            self.cmd
        )
        with self.assertRaisesBusinessException(exception.MiniTrainingNotFoundException):
            self.fake_mini_training_repository.get(entity_identity_of_deleted_mini_training)

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

from django.test import TestCase

from education_group.ddd import command
from education_group.ddd.domain import exception
from education_group.ddd.service.write import delete_orphan_training_service
from education_group.tests.ddd.factories.repository.fake import get_fake_training_repository
from education_group.tests.ddd.factories.training import TrainingFactory
from testing.mocks import MockPatcherMixin


class TestDeleteOrphanTraining(TestCase, MockPatcherMixin):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = command.DeleteOrphanTrainingCommand(
            year=2018,
            acronym="MAP29"
        )

    def setUp(self) -> None:
        self.training_2018 = TrainingFactory(
            entity_identity__acronym=self.cmd.acronym,
            entity_identity__year=self.cmd.year
        )
        self.fake_training_repo = get_fake_training_repository([self.training_2018])
        self.mock_repo(
            "education_group.ddd.repository.training.TrainingRepository",
            self.fake_training_repo
        )

    def test_should_return_entity_identity_of_deleted_training(self):
        result = delete_orphan_training_service.delete_orphan_training(self.cmd)

        expected_result = self.training_2018.entity_id
        self.assertEqual(expected_result, result)

    def test_should_remove_training_from_repository(self):
        entity_identity_of_deleted_training = delete_orphan_training_service.delete_orphan_training(self.cmd)
        with self.assertRaises(exception.TrainingNotFoundException):
            self.fake_training_repo.get(entity_identity_of_deleted_training)

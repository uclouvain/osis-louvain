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
import mock
from django.test import SimpleTestCase

from education_group.ddd.domain import mini_training, exception
from education_group.tests.factories.factories.command import CreateOrphanMiniTrainingCommandFactory
from education_group.tests.factories.mini_training import MiniTrainingFactory
from testing import mocks


class TestMiniTrainingBuilder(SimpleTestCase):
    def setUp(self):
        self.command = CreateOrphanMiniTrainingCommandFactory()

    @mock.patch("education_group.ddd.validators.validators_by_business_action.CreateMiniTrainingValidatorList.validate")
    def test_should_derive_values_from_command_when_build_from_command(self, mock_validator):
        mock_validator.return_value = None

        result = mini_training.MiniTrainingBuilder.build_from_create_cmd(self.command)
        self.assertIsInstance(result, mini_training.MiniTraining)
        self.assertTrue(mock_validator.called)


class TestMiniTrainingBuilderCopyToNextYear(SimpleTestCase):
    @mock.patch("education_group.ddd.repository.mini_training.MiniTrainingRepository",
                new_callable=mocks.MockRepository)
    def test_should_return_existing_training_when_training_exists_for_next_year(self, mock_repository):
        mini_training_source = MiniTrainingFactory()
        mini_training_next_year = MiniTrainingFactory()

        mock_repository.get.return_value = mini_training_next_year

        result = mini_training.MiniTrainingBuilder().copy_to_next_year(mini_training_source, mock_repository)

        self.assertEqual(mini_training_next_year, result)

    @mock.patch("education_group.ddd.repository.mini_training.MiniTrainingRepository", new_callable=mocks.MockRepository)
    def test_should_copy_with_increment_year_when_training_does_not_exists_for_next_year(self, mock_repository):
        mini_training_source = MiniTrainingFactory()

        mock_repository.get.side_effect = exception.MiniTrainingNotFoundException

        result = mini_training.MiniTrainingBuilder().copy_to_next_year(mini_training_source, mock_repository)

        self.assertEqual(mini_training_source.entity_id.year + 1, result.entity_id.year)

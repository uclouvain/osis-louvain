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
from django.test import TestCase

from education_group.ddd import command
from education_group.ddd.service.write import copy_training_service
from education_group.tests.ddd.factories.training import TrainingFactory


class TestCopyTrainingToNextYear(TestCase):
    @mock.patch("education_group.ddd.service.write.copy_training_service.TrainingRepository")
    @mock.patch("education_group.ddd.service.write.copy_training_service.TrainingBuilder")
    def test_should_create_a_copy_for_next_year(
            self,
            mock_builder,
            mock_repository):
        source_training = TrainingFactory()
        next_year_training = TrainingFactory()
        mock_repository.return_value.get.return_value = source_training
        mock_repository.return_value.create.return_value = next_year_training.entity_id
        mock_builder.return_value.copy_to_next_year.return_value = next_year_training

        cmd = command.CopyTrainingToNextYearCommand(acronym="ACRONYM", postpone_from_year=2018)
        result = copy_training_service.copy_training_to_next_year(cmd)

        self.assertEqual(next_year_training.entity_id, result)

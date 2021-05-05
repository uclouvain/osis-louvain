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
from education_group.ddd.service.read import get_training_service
from education_group.tests.ddd.factories.training import TrainingFactory
from testing.testcases import DDDTestCase


class TestGetTraining(DDDTestCase):
    def setUp(self):
        super().setUp()
        self.training = TrainingFactory(persist=True)
        self.cmd = command.GetTrainingCommand(year=self.training.year, acronym=self.training.acronym)

    def test_throw_exception_when_no_matching_mini_training(self):
        cmd = command.GetTrainingCommand(year=self.training.year + 1, acronym=self.training.acronym)
        with self.assertRaisesBusinessException(exception.TrainingNotFoundException):
            get_training_service.get_training(cmd)

    def test_return_matching_mini_training(self):
        result = get_training_service.get_training(self.cmd)
        self.assertEqual(self.training, result)

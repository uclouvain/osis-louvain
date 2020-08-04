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

from base.tests.factories.academic_year import AcademicYearFactory
from education_group.ddd import command
from education_group.ddd.domain import training
from education_group.ddd.service.write import postpone_training_service
from education_group.tests.ddd.factories.training import TrainingFactory
from testing import mocks


class TestPostponeTraining(TestCase):
    @mock.patch("education_group.ddd.service.write.postpone_training_service.TrainingRepository",
                new_callable=mocks.MockRepository)
    @mock.patch("education_group.ddd.domain.service.calculate_end_postponement."
                "CalculateEndPostponement.calculate_year_of_end_postponement", return_value=2021)
    @mock.patch("education_group.ddd.service.write.copy_training_service.copy_training_to_next_year")
    def test_should_return_a_number_of_identities_equal_to_difference_of_from_year_and_until_year(
            self,
            mock_copy_training_to_next_year_service,
            mock_calculate_end_year_of_postponement,
            mock_repostirory):
        training_identities = [
            training.TrainingIdentity(acronym="ACRO", year=2018),
            training.TrainingIdentity(acronym="ACRO", year=2019),
            training.TrainingIdentity(acronym="ACRO", year=2020)
        ]
        mock_copy_training_to_next_year_service.side_effect = training_identities
        mock_repostirory.return_value.get.return_value = TrainingFactory()

        cmd = command.PostponeTrainingCommand(acronym="ACRO", postpone_from_year=2018)
        result = postpone_training_service.postpone_training(cmd)
        self.assertListEqual(training_identities, result)

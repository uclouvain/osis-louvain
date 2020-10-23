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
from copy import copy, deepcopy

import mock
from django.test import SimpleTestCase

from education_group.ddd.domain import training, exception
from education_group.ddd.domain._co_organization import Coorganization
from education_group.ddd.domain.exception import MaximumCertificateAimType2Reached
from education_group.tests.ddd.factories.co_organization import CoorganizationFactory
from education_group.tests.ddd.factories.diploma import DiplomaFactory, DiplomaAimFactory, DiplomaAimIdentityFactory
from education_group.tests.ddd.factories.training import TrainingFactory


class TestTrainingBuilderCopyToNextYear(SimpleTestCase):
    @mock.patch("education_group.ddd.repository.training.TrainingRepository", autospec=True)
    def test_should_return_existing_training_when_training_exists_for_next_year(self, mock_repository):
        training_source = TrainingFactory()
        training_next_year = TrainingFactory()

        mock_repository.get.return_value = training_next_year

        result = training.TrainingBuilder().copy_to_next_year(training_source, mock_repository)

        self.assertEqual(training_next_year, result)

    @mock.patch("education_group.ddd.repository.training.TrainingRepository", autospec=True)
    def test_should_copy_with_increment_year_when_training_does_not_exists_for_next_year(self, mock_repository):
        training_source = TrainingFactory()

        mock_repository.get.side_effect = exception.TrainingNotFoundException

        result = training.TrainingBuilder().copy_to_next_year(training_source, mock_repository)

        self.assertEqual(training_source.entity_id.year + 1, result.entity_id.year)
        self.assertEqual(training_source.identity_through_years, result.identity_through_years)

    @mock.patch("education_group.ddd.repository.training.TrainingRepository", autospec=True)
    @mock.patch("education_group.ddd.domain.training.Training.update_aims_from_other_training")
    def test_should_call_update_aims_from_other_training_when_copy_aims_to_next_year(
            self,
            mock_update_aims,
            mock_repository
    ):
        training_source = TrainingFactory()
        training_next_year = TrainingFactory()

        mock_repository.get.return_value = training_next_year

        training.TrainingBuilder().copy_aims_to_next_year(training_source, mock_repository)
        self.assertTrue(mock_update_aims.called)


class TestTrainingHasSameValuesAs(SimpleTestCase):
    def test_should_return_false_when_values_are_different(self):
        training_source = TrainingFactory()
        other_training = TrainingFactory()

        self.assertFalse(training_source.has_same_values_as(other_training))

    def test_should_return_true_when_values_are_equal(self):
        training_source = TrainingFactory()
        other_training = copy(training_source)

        self.assertTrue(training_source, other_training)

    def test_should_ignore_coorganization_has_conflicted_fields_if_different(self):
        training_source = TrainingFactory()
        other_training = deepcopy(training_source)
        other_training.co_organizations = [CoorganizationFactory()]

        self.assertTrue(training_source.has_same_values_as(other_training))


class TestTrainingHasConflictedCertificateAims(SimpleTestCase):
    def test_should_return_true_when_values_are_different(self):
        training_source = TrainingFactory(diploma=DiplomaFactory(aims=['dummy_aim']))
        other_training = TrainingFactory(diploma=DiplomaFactory(aims=['other_aim']))

        self.assertTrue(training_source.has_conflicted_certificate_aims(other_training))

    def test_should_return_false_when_values_are_equal(self):
        training_source = TrainingFactory(diploma=DiplomaFactory(aims=['dummy_aim']))
        other_training = TrainingFactory(diploma=DiplomaFactory(aims=['dummy_aim']))

        self.assertFalse(training_source.has_conflicted_certificate_aims(other_training))


class TestUpdateCertificateAims(SimpleTestCase):
    def test_should_return_max_type_2_aims_error(self):
        training_source = TrainingFactory(
            diploma=DiplomaFactory(
                aims=[DiplomaAimFactory(entity_id=DiplomaAimIdentityFactory(section=2)) for _ in range(2)]
            )
        )

        with self.assertRaises(MaximumCertificateAimType2Reached):
            training_source.update_aims(data=training.UpdateDiplomaData(diploma=training_source.diploma))

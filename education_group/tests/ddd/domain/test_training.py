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
from testing.testcases import DDDTestCase


class TestTrainingHasSameValuesAs(DDDTestCase):
    def test_should_return_false_when_values_are_different(self):
        training_source = TrainingFactory(persist=True)
        other_training = TrainingFactory(persist=True)

        self.assertFalse(training_source.has_same_values_as(other_training))

    def test_should_return_true_when_values_are_equal(self):
        training_source = TrainingFactory(persist=True)
        other_training = copy(training_source)

        self.assertTrue(training_source, other_training)

    def test_should_ignore_coorganization_has_conflicted_fields_if_different(self):
        training_source = TrainingFactory(persist=True)
        other_training = deepcopy(training_source)
        other_training.co_organizations = [CoorganizationFactory()]

        self.assertTrue(training_source.has_same_values_as(other_training))


class TestTrainingHasConflictedCertificateAims(DDDTestCase):
    def test_should_return_true_when_values_are_different(self):
        training_source = TrainingFactory(diploma=DiplomaFactory(aims=['dummy_aim']), persist=True)
        other_training = TrainingFactory(diploma=DiplomaFactory(aims=['other_aim']), persist=True)

        self.assertTrue(training_source.has_conflicted_certificate_aims(other_training))

    def test_should_return_false_when_values_are_equal(self):
        training_source = TrainingFactory(diploma=DiplomaFactory(aims=['dummy_aim']), persist=True)
        other_training = TrainingFactory(diploma=DiplomaFactory(aims=['dummy_aim']), persist=True)

        self.assertFalse(training_source.has_conflicted_certificate_aims(other_training))

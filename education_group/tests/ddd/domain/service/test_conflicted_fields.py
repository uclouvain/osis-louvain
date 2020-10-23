##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase

from education_group.ddd.domain.service.conflicted_fields import ConflictedFields
from education_group.tests.ddd.factories.diploma import DiplomaFactory
from education_group.tests.ddd.factories.repository.fake import get_fake_training_repository
from education_group.tests.ddd.factories.training import TrainingFactory
from testing.mocks import MockPatcherMixin


class TestConflictedCertificateAims(TestCase, MockPatcherMixin):
    def setUp(self):
        self.acronym = 'ACR00'
        self.year = 2020
        self.trainings = [
            TrainingFactory(entity_identity__acronym=self.acronym, entity_identity__year=year)
            for year in range(self.year, self.year + 5)
        ]
        self.fake_training_repository = get_fake_training_repository(self.trainings)
        self.mock_repo(
            "education_group.ddd.domain.service.conflicted_fields.TrainingRepository",
            self.fake_training_repository
        )
        self.aims = ['dummy_aim']

    def test_should_return_no_conflicted_certificate_aims(self):
        conflicted_aims = ConflictedFields.get_conflicted_certificate_aims(self.trainings[0].entity_identity)
        self.assertEqual(conflicted_aims, [])

    def test_should_return_conflicted_certificate_aims(self):
        conflicted_year_index = 2
        self.trainings[conflicted_year_index] = TrainingFactory(
            entity_identity__acronym=self.acronym,
            entity_identity__year=self.year + conflicted_year_index,
            diploma=DiplomaFactory(aims=self.aims)
        )
        self.fake_training_repository.root_entities = self.trainings
        conflicted_aims = ConflictedFields.get_conflicted_certificate_aims(self.trainings[0].entity_identity)
        self.assertEqual(conflicted_aims, [self.year + conflicted_year_index])

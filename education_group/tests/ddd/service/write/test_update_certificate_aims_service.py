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

from education_group.ddd.domain import training
from education_group.ddd.service.write import update_certificate_aims_service
from education_group.tests.ddd.factories.command.update_certificate_aims_command import \
    UpdateCertificateAimsCommandFactory
from education_group.tests.ddd.factories.diploma import DiplomaAimIdentityFactory
from education_group.tests.ddd.factories.repository.fake import get_fake_training_repository
from education_group.tests.ddd.factories.training import TrainingFactory
from testing.mocks import MockPatcherMixin


class TestUpdateCertificateAims(TestCase, MockPatcherMixin):
    @classmethod
    def setUpTestData(cls):
        cls.aim = DiplomaAimIdentityFactory()
        cls.cmd = UpdateCertificateAimsCommandFactory(aims=[(cls.aim.code, cls.aim.section)])

    def setUp(self) -> None:
        self.trainings = [
            TrainingFactory(entity_identity__acronym=self.cmd.acronym, entity_identity__year=self.cmd.year)
        ]
        self.fake_training_repo = get_fake_training_repository(self.trainings)
        self.mock_repo("education_group.ddd.repository.training.TrainingRepository", self.fake_training_repo)

    def test_should_return_entity_id_of_updated_training(self):
        result = update_certificate_aims_service.update_certificate_aims(self.cmd)

        expected_result = training.TrainingIdentity(acronym=self.cmd.acronym, year=self.cmd.year)
        self.assertEqual(expected_result, result)


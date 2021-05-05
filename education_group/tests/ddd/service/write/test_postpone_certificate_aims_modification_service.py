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

import attr

from education_group.ddd import command
from education_group.ddd.domain.exception import MaximumCertificateAimType2Reached, \
    CertificateAimsCopyConsistencyException
from education_group.ddd.domain.training import Training
from education_group.ddd.service.write import postpone_certificate_aims_modification_service
from education_group.tests.ddd.factories.diploma import DiplomaFactory
from education_group.tests.ddd.factories.training import TrainingFactory
from testing.testcases import DDDTestCase


class TestPostponeCertificateAims(DDDTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.trainings = TrainingFactory.multiple(3, persist=True)
        self.cmd = command.PostponeCertificateAimsCommand(
            postpone_from_acronym=self.trainings[0].acronym,
            postpone_from_year=self.trainings[0].entity_identity.year,
            aims=[(1, 2)]
        )
        self.mock_service(
            "program_management.ddd.domain.service.calculate_end_postponement.CalculateEndPostponement."
            "calculate_end_postponement_year_training",
            self.trainings[0].year + 3
        )

    def test_cannot_have_more_than_one_certificate_aim_of_section_2(self):
        cmd = attr.evolve(self.cmd, aims=[(1, 2), (4, 2)])

        with self.assertRaisesBusinessException(MaximumCertificateAimType2Reached):
            postpone_certificate_aims_modification_service.postpone_certificate_aims_modification(cmd)

    def test_should_empty_certificate_aims_if_none_given_of_trainings_from_year(self):
        cmd = attr.evolve(self.cmd, aims=None)

        identities = postpone_certificate_aims_modification_service.postpone_certificate_aims_modification(cmd)

        for identity in identities:
            updated_training = self.fake_training_repository.get(identity)

            self.assert_training_certificate_aims_match_command(updated_training, cmd)

    def test_should_update_certificate_aims_of_trainings_from_year(self):
        identities = postpone_certificate_aims_modification_service.postpone_certificate_aims_modification(self.cmd)

        for identity in identities:
            updated_training = self.fake_training_repository.get(identity)

            self.assert_training_certificate_aims_match_command(updated_training, self.cmd)

    def test_should_return_training_identities(self):
        result = postpone_certificate_aims_modification_service.postpone_certificate_aims_modification(self.cmd)

        expected_identities = [training.entity_id for training in self.trainings]
        self.assertListEqual(expected_identities, result)

    def test_should_not_update_certificate_aims_of_trainings_with_conflicts_with_previous_year(self):
        self.trainings[2].diploma = DiplomaFactory(with_aims=True)

        with self.assertRaisesBusinessException(CertificateAimsCopyConsistencyException) as e:
            postpone_certificate_aims_modification_service.postpone_certificate_aims_modification(self.cmd)

        self.assertEqual(self.trainings[2].year, e.exception.conflicted_fields_year)

    def assert_training_certificate_aims_match_command(
            self,
            training: 'Training',
            cmd: 'command.PostponeCertificateAimsCommand'):
        if not cmd.aims:
            self.assertListEqual([], training.diploma.aims)
        else:
            diploma_aims = [(aim.code, aim.section) for aim in training.diploma.aims]
            self.assertEqual(self.cmd.aims, diploma_aims)

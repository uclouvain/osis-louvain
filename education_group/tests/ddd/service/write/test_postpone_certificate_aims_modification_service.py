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
from unittest import mock

from django.test import SimpleTestCase

from education_group.ddd.domain.exception import CertificateAimsCopyConsistencyException
from education_group.ddd.service.write import postpone_certificate_aims_modification_service
from education_group.tests.ddd.factories.command.postpone_certificacte_aims_command import \
    PostponeCertificateAimsCommandFactory
from education_group.tests.ddd.factories.training import TrainingIdentityFactory


class TestPostponeCertificateAimsModificationService(SimpleTestCase):
    def setUp(self) -> None:
        self.training_identity = TrainingIdentityFactory()
        self.cmd = PostponeCertificateAimsCommandFactory(
            postpone_from_year=self.training_identity.year,
            aims=['dummy_aim']
        )
        self.end_postponement_year = self.training_identity.year + 1

    @mock.patch('education_group.ddd.service.write.update_certificate_aims_service.update_certificate_aims')
    @mock.patch('program_management.ddd.domain.service.calculate_end_postponement.CalculateEndPostponement.'
                'calculate_end_postponement_year_training')
    @mock.patch('education_group.ddd.service.write.copy_certificate_aims_service.copy_certificate_aims_to_next_year')
    @mock.patch('education_group.ddd.domain.service.conflicted_fields.ConflictedFields.get_conflicted_certificate_aims')
    def test_postpone_certificate_aims(
            self,
            mock_get_conflicted_fields,
            mock_copy_certificate_aims,
            mock_calculate_end_postponement_year,
            mock_update_aims,
    ):
        mock_get_conflicted_fields.return_value = []
        mock_update_aims.return_value = self.training_identity
        mock_calculate_end_postponement_year.return_value = self.end_postponement_year

        updated_trainings_in_future = [
            TrainingIdentityFactory(year=year)
            for year in range(self.training_identity.year, self.end_postponement_year)
        ]
        mock_copy_certificate_aims.side_effect = updated_trainings_in_future

        result = postpone_certificate_aims_modification_service.postpone_certificate_aims_modification(self.cmd)

        self.assertEqual([self.training_identity] + updated_trainings_in_future, result)

    @mock.patch('education_group.ddd.service.write.update_certificate_aims_service.update_certificate_aims')
    @mock.patch('program_management.ddd.domain.service.calculate_end_postponement.CalculateEndPostponement.'
                'calculate_end_postponement_year_training')
    @mock.patch('education_group.ddd.domain.service.conflicted_fields.ConflictedFields.get_conflicted_certificate_aims')
    def test_postpone_raise_exception_when_conflicted_aims_in_future_years(
            self,
            mock_get_conflicted_fields,
            mock_calculate_end_postponement_year,
            mock_update_aims,
    ):
        mock_get_conflicted_fields.return_value = [self.end_postponement_year]
        mock_update_aims.return_value = self.training_identity
        mock_calculate_end_postponement_year.return_value = self.end_postponement_year

        with self.assertRaises(CertificateAimsCopyConsistencyException):
            postpone_certificate_aims_modification_service.postpone_certificate_aims_modification(self.cmd)

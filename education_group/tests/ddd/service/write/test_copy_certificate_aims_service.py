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
from education_group.ddd.domain import training
from education_group.ddd.service.write import copy_certificate_aims_service
from education_group.tests.ddd.factories.training import TrainingFactory
from testing.testcases import DDDTestCase


# FIXME delete this test as this application service is not used directly
class TestCopyCertificateAimsToNextYear(DDDTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.year = 2020
        cls.cmd = command.CopyCertificateAimsToNextYearCommand(
            acronym="ACRONYM",
            postpone_from_year=cls.year
        )

    def setUp(self) -> None:
        super().setUp()
        self.trainings = [
            TrainingFactory(
                entity_identity__acronym=self.cmd.acronym,
                entity_identity__year=year,
                persist=True
            ) for year in [self.year, self.year+1]
        ]

    def test_should_return_identity(self):
        result = copy_certificate_aims_service.copy_certificate_aims_to_next_year(self.cmd)

        expected_result = training.TrainingIdentity(acronym="ACRONYM", year=self.year+1)
        self.assertEqual(expected_result, result)

    def test_should_return_none_on_training_not_found_exception(self):
        cmd = command.CopyCertificateAimsToNextYearCommand(acronym="ACRONYM", postpone_from_year=self.year+1)

        result = copy_certificate_aims_service.copy_certificate_aims_to_next_year(cmd)
        self.assertIsNone(result)

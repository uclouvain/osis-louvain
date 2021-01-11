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
from django.test import SimpleTestCase

from education_group.ddd.command import GetTrainingEmptyFieldsOnWarningCommand
from education_group.ddd.domain import exception
from education_group.ddd.service.read.check_training_empty_fields_on_warning_service import \
    check_training_empty_fields_on_warning
from education_group.tests.ddd.factories.funding import FundingFactory
from education_group.tests.ddd.factories.repository.fake import get_fake_training_repository
from education_group.tests.ddd.factories.training import TrainingFactory
from testing.mocks import MockPatcherMixin


class TestCheckEmptyFields(SimpleTestCase, MockPatcherMixin):
    def setUp(self):
        self.training = TrainingFactory()
        fake_training_repository = get_fake_training_repository([self.training])
        self.mock_repo("education_group.ddd.repository.training.TrainingRepository", fake_training_repository)

        self.command = GetTrainingEmptyFieldsOnWarningCommand(
            acronym=self.training.entity_id.acronym,
            year=self.training.entity_id.year
        )

        self.mock_service(
            "education_group.ddd.domain.service.fields_with_alert_when_empty.get_for_training",
            ["funding_orientation"]
        )

    def test_should_not_return_exception_when_no_empty_fields(self):
        result = check_training_empty_fields_on_warning(self.command)

        self.assertEqual(result, None)

    def test_should_raise_exception_when_empty_fields(self):
        self.training.main_domain = None
        self.training.funding = FundingFactory(funding_orientation=None)

        with self.assertRaises(exception.TrainingEmptyFieldException):
            check_training_empty_fields_on_warning(self.command)

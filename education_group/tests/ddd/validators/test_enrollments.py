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
import mock
from django.test import SimpleTestCase

from education_group.ddd.domain.exception import TrainingHaveEnrollments, MiniTrainingHaveEnrollments
from education_group.ddd.domain.training import TrainingIdentity
from education_group.ddd.validators._enrollments import TrainingEnrollmentsValidator, MiniTrainingEnrollmentsValidator


class TestTrainingEnrollmentsValidator(SimpleTestCase):
    def setUp(self) -> None:
        self.training_id = TrainingIdentity(acronym="AGRO2M", year=2014)

    @mock.patch(
        'education_group.ddd.validators._enrollments.EnrollmentCounter.get_training_enrollments_count',
        return_value=3
    )
    def test_assert_raise_exception_case_training_have_enrollments(self, mock_get_enrollments_count):
        validator = TrainingEnrollmentsValidator(self.training_id)
        with self.assertRaises(TrainingHaveEnrollments):
            validator.is_valid()

    @mock.patch(
        'education_group.ddd.validators._enrollments.EnrollmentCounter.get_training_enrollments_count',
        return_value=0
    )
    def test_assert_not_raise_exception_when_training_have_no_enrollment(self, mock_get_enrollments_count):
        validator = TrainingEnrollmentsValidator(self.training_id)
        self.assertTrue(validator.is_valid())


# class TestMiniTrainingEnrollmentsValidator(SimpleTestCase):
#     def setUp(self) -> None:
#         self.mini_training_id = MiniTrainingIdentity(acronym="OPTIO500M", year=2014)
#
#     @mock.patch(
#         'education_group.ddd.validators._enrollments.EnrollmentCounter.get_mini_training_enrollments_count',
#         return_value=3
#     )
#     def test_assert_raise_exception_case_mini_training_have_enrollments(self, mock_get_enrollments_count):
#         validator = MiniTrainingEnrollmentsValidator(self.mini_training_id)
#         with self.assertRaises(MiniTrainingHaveEnrollments):
#             validator.is_valid()
#
#     @mock.patch(
#         'education_group.ddd.validators._enrollments.EnrollmentCounter.get_training_enrollments_count',
#         return_value=0
#     )
#     def test_assert_not_raise_exception_when_mini_training_have_no_enrollment(self, mock_get_enrollments_count):
#         validator = MiniTrainingEnrollmentsValidator(self.training_id)
#         self.assertTrue(validator.is_valid())

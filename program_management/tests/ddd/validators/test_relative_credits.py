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
from django.test import SimpleTestCase

from program_management.ddd.domain.exception import RelativeCreditShouldBeGreaterOrEqualsThanZero

from program_management.ddd.validators._relative_credits import RelativeCreditsValidator


class TestRelativeCreditsValidator(SimpleTestCase):
    def test_assert_raise_exception_case_relative_credits_lower_than_zero(self):
        validator = RelativeCreditsValidator(-1)
        with self.assertRaises(RelativeCreditShouldBeGreaterOrEqualsThanZero):
            validator.is_valid()

    def test_assert_relative_credits_must_be_greater_or_equals_to_zero(self):
        validator = RelativeCreditsValidator(0)
        self.assertTrue(validator.is_valid())

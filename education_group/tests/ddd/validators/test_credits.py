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

from education_group.ddd.domain.exception import CreditShouldBeGreaterOrEqualsThanZero

from education_group.ddd.validators._credits import CreditsValidator


class TestCreditsValidator(SimpleTestCase):
    def test_assert_raise_exception_case_credits_lower_than_zero(self):
        validator = CreditsValidator(-1)
        with self.assertRaises(CreditShouldBeGreaterOrEqualsThanZero):
            validator.is_valid()

    def test_assert_credits_must_be_greater_or_equals_to_zero(self):
        validator = CreditsValidator(0)
        self.assertTrue(validator.is_valid())

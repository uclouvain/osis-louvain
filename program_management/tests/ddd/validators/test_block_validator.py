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
from django.utils.translation import gettext_lazy as _

from program_management.ddd.validators import _block_validator
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestBlockValidator(TestValidatorValidateMixin, SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.error_msg = _(
            "Please register a maximum of %(max_authorized_value)s digits in ascending order, "
            "without any duplication. Authorized values are from 1 to 6. Examples: 12, 23, 46"
        ) % {'max_authorized_value': _block_validator.BLOCK_MAX_AUTHORIZED_VALUE}

    def test_when_block_value_is_none_then_should_not_raise_exception(self):
        self.assertValidatorNotRaises(_block_validator.BlockValidator(None))

    def test_should_raise_exception_when_block_value_is_composed_of_digit_not_comprised_between_1_and_6(self):
        block_inputs = [1257, 49]
        for input in block_inputs:
            with self.subTest(block=input):
                self.assertValidatorRaises(_block_validator.BlockValidator(input), [self.error_msg])

    def test_should_raise_exception_when_block_value_is_a_sequence_of_digits_that_are_not_in_increasing_order(self):
        block_inputs = [265, 132]
        for input in block_inputs:
            with self.subTest(block=input):
                self.assertValidatorRaises(_block_validator.BlockValidator(input), [self.error_msg])

    def test_should_not_raise_exception_when_block_value_is_an_increasing_sequence_of_digits_comprised_between_1_and_6(
            self
    ):
        block_inputs = [123456, 5, 46, 1345]
        for input in block_inputs:
            with self.subTest(block=input):
                self.assertValidatorNotRaises(_block_validator.BlockValidator(input))

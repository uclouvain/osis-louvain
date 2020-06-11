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

from program_management.ddd.validators import _block_validator


class TestBlockValidator(SimpleTestCase):
    def test_block_value_should_accept_none_value(self):
        validator = _block_validator.BlockValidator(None)
        self.assertTrue(validator.is_valid())

    def test_block_value_should_not_accept_number_not_comprised_between_1_and_6(self):
        block_inputs = [1257, 49]
        for input in block_inputs:
            with self.subTest(block=input):
                validator = _block_validator.BlockValidator(input)
                self.assertFalse(validator.is_valid())

    def test_block_value_should_not_accept_sequence_of_digits_that_are_not_in_increasing_order(self):
        block_inputs = [265, 132]
        for input in block_inputs:
            with self.subTest(block=input):
                validator = _block_validator.BlockValidator(input)
                self.assertFalse(validator.is_valid())

    def test_block_value_should_accept_increasing_sequence_of_digits_comprised_between_1_and_6(self):
        block_inputs = [123456, 5, 46, 1345]
        for input in block_inputs:
            with self.subTest(block=input):
                validator = _block_validator.BlockValidator(input)
                self.assertTrue(validator.is_valid())

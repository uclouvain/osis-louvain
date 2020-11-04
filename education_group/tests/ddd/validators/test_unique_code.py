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

from education_group.ddd.domain.exception import CodeAlreadyExistException
from education_group.ddd.validators._unique_code import UniqueCodeValidator


class TestUniqueCodeValidator(SimpleTestCase):
    @mock.patch('education_group.ddd.validators._unique_code.CheckCodeExist.get_existing_year', return_value=2020)
    def test_assert_raise_exception_when_code_exist(self, mock_get_existing_year):
        validator = UniqueCodeValidator("DUMMY")
        with self.assertRaises(CodeAlreadyExistException):
            validator.is_valid()

    @mock.patch('education_group.ddd.validators._unique_code.CheckCodeExist.get_existing_year', return_value=None)
    def test_assert_not_raise_exception_when_code_not_exist(self, mock_get_existing_year):
        validator = UniqueCodeValidator("DUMMY")
        self.assertTrue(validator.is_valid())

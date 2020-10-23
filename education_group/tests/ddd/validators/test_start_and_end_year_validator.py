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

from education_group.ddd.domain import exception
from education_group.ddd.validators import start_and_end_year_validator


class TestStartAndEndYearValidator(SimpleTestCase):
    def test_should_raise_exception_when_start_year_strictly_superior_than_end_year(self):
        with self.assertRaises(exception.StartYearGreaterThanEndYearException):
            start_and_end_year_validator.StartAndEndYearValidator(2019, 2018).validate()

    def test_should_not_raise_exception_when_start_year_inferior_to_end_year(self):
        result = start_and_end_year_validator.StartAndEndYearValidator(2017, 2018).validate()
        self.assertIsNone(result)

    def test_should_not_raise_exception_when_start_year_equal_to_end_year(self):
        result = start_and_end_year_validator.StartAndEndYearValidator(2018, 2018).validate()
        self.assertIsNone(result)

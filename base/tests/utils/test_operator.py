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

from base.utils import operator


class TestIsYearLower(SimpleTestCase):
    def test_should_return_false_when_base_year_is_none(self):
        self.assertFalse(
            operator.is_year_lower(None, 2025)
        )

    def test_should_return_true_when_year_to_compare_to_is_none(self):
        self.assertTrue(
            operator.is_year_lower(2029, None)
        )

    def test_should_return_true_when_base_year_is_inferior_to_other_year(self):
        self.assertTrue(
            operator.is_year_lower(2017, 2029)
        )

    def test_should_return_false_when_base_year_is_equal_to_other_year(self):
        self.assertFalse(
            operator.is_year_lower(2017, 2017)
        )

    def test_should_return_false_when_base_year_is_greater_to_other_year(self):
        self.assertFalse(
            operator.is_year_lower(2019, 2017)
        )

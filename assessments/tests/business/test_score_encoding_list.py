##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import decimal

from django.test import TestCase

from assessments.business import score_encoding_list


class TestConvertToDecimal(TestCase):
    """Unit tests on _convert_to_decimal()"""

    def test_when_2_decimals_in_encoded_score(self):
        result = score_encoding_list._convert_to_decimal(float(15.55), True)
        self.assertIsInstance(result, decimal.Decimal)
        self.assertEqual(str(result), '15.55')

    def test_when_3_decimals_in_encoded_score(self):
        with self.assertRaises(ValueError):
            score_encoding_list._convert_to_decimal(float(15.555), True)

    def test_when_deciamls_unauthorized(self):
        with self.assertRaises(ValueError):
            score_encoding_list._convert_to_decimal(float(15.555), False)

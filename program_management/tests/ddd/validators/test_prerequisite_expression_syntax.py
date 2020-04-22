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

from program_management.ddd.validators._prerequisite_expression_syntax import PrerequisiteExpressionSyntaxValidator


class TestPrerequisiteExpressionSyntaxValidator(SimpleTestCase):
    def test_empty_string(self):
        self.assertTrue(PrerequisiteExpressionSyntaxValidator("").is_valid())

    def test_acronym_cannot_include_space(self):
        self.assertFalse(PrerequisiteExpressionSyntaxValidator("LSINF 1111").is_valid())

    def test_acronym_syntax(self):
        self.assertFalse(PrerequisiteExpressionSyntaxValidator("LILKNLJLJFD48464").is_valid())

    def test_can_only_have_one_main_operator(self):
        self.assertFalse(PrerequisiteExpressionSyntaxValidator("LSINF1111 ET LINGI152 OU LINGI2356").is_valid())

    def test_main_and_secondary_operators_must_be_different(self):
        self.assertFalse(PrerequisiteExpressionSyntaxValidator("LSINF1111 OU (LINGI1526 OU LINGI2356)").is_valid())

    def test_group_must_have_at_least_two_elements(self):
        self.assertFalse(PrerequisiteExpressionSyntaxValidator("LSINF1111 ET (LINGI152)").is_valid())

    def test_cannot_have_unique_element_as_a_group(self):
        self.assertFalse(PrerequisiteExpressionSyntaxValidator("(LSINF1111 ET LINGI2315)").is_valid())

    def test_with_prerequisites_correctly_encoded(self):
        test_values = (
            "LSINF1111 ET LINGI1452 ET LINGI2356",
            "LSINF1111 OU LINGI1452 OU LINGI2356",
            "LSINF1111 ET (LINGI1526B OU LINGI2356)",
            "LSINF1111 OU (LINGI1526 ET LINGI2356) OU (LINGI1552 ET LINGI2347)",
            "LSINF1111 ET (LINGI1152 OU LINGI1526 OU LINGI2356)",
            "(LINGI1526 ET LINGI2356) OU LINGI1552 OU LINGI2347",
            "LINGI2145",
            "LINGI2145A",
        )
        for test_value in test_values:
            with self.subTest(good_prerequisite=test_value):
                self.assertTrue(PrerequisiteExpressionSyntaxValidator(test_value).is_valid())

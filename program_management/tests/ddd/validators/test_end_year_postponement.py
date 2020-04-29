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
from django.utils.translation import gettext as _

from program_management.ddd.validators._end_year_postponement import EndYearPostponementValidator
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestEndYearPostponementValidator(SimpleTestCase):

    def setUp(self):
        self.end_postponement_year = 2020

    def test_when_year_of_the_tree_to_fill_in_is_lower_than_end_postponement_year(self):
        tree_to_fill_in = ProgramTreeFactory(root_node__year=self.end_postponement_year - 1)
        validator = EndYearPostponementValidator(tree_to_fill_in, self.end_postponement_year)
        self.assertTrue(validator.is_valid())

    def test_when_year_of_the_tree_to_fill_in_is_equal_to_end_postponement_year(self):
        tree_to_fill_in = ProgramTreeFactory(root_node__year=self.end_postponement_year)
        validator = EndYearPostponementValidator(tree_to_fill_in, self.end_postponement_year)
        self.assertTrue(validator.is_valid())

    def test_when_year_of_the_tree_to_fill_in_is_greater_than_end_postponement_year(self):
        tree_to_fill_in = ProgramTreeFactory(root_node__year=self.end_postponement_year + 1)
        validator = EndYearPostponementValidator(tree_to_fill_in, self.end_postponement_year)
        self.assertFalse(validator.is_valid())
        expected_result = _("The end date of the education group is smaller than the year of postponement.")
        self.assertListEqual([expected_result], validator.error_messages)

    def test_when_end_postponement_is_none(self):
        tree_to_fill_in = ProgramTreeFactory(root_node__year=self.end_postponement_year)
        validator = EndYearPostponementValidator(tree_to_fill_in, None)
        self.assertTrue(validator.is_valid())

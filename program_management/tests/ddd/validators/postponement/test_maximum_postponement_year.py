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

from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from program_management.ddd.validators.postponement._min_max_postponement_year import MinimumMaximumPostponementYearValidator
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestMinimumMaximumPostponementYearValidator(SimpleTestCase):

    def setUp(self):
        self.current_working_year = 2020
        self._patch_current_working_year()

    def _patch_current_working_year(self):
        patcher_current_working_year = patch("program_management.ddd.repositories.load_working_academic_year.load")
        self.addCleanup(patcher_current_working_year.stop)
        self.mock_year = patcher_current_working_year.start()
        self.mock_year.return_value = self.current_working_year

    def test_when_year_of_tree_to_fill_in_is_past(self):
        tree_to_fill_in = ProgramTreeFactory(root_node__year=self.current_working_year - 1)
        validator = MinimumMaximumPostponementYearValidator(tree_to_fill_in)
        self.assertFalse(validator.is_valid())
        expected_result = _("You are not allowed to postpone this training in the past.")
        self.assertListEqual([expected_result], validator.error_messages)

    def test_when_year_of_tree_to_fill_in_equals_current_year(self):
        tree_to_fill_in = ProgramTreeFactory(root_node__year=self.current_working_year)
        validator = MinimumMaximumPostponementYearValidator(tree_to_fill_in)
        self.assertTrue(validator.is_valid())

    def test_when_year_of_tree_to_fill_in_greater_1_than_current_year(self):
        tree_to_fill_in = ProgramTreeFactory(root_node__year=self.current_working_year + 1)
        validator = MinimumMaximumPostponementYearValidator(tree_to_fill_in)
        self.assertTrue(validator.is_valid())

    def test_when_year_of_tree_to_fill_in_greater_2_than_current_year(self):
        tree_to_fill_in = ProgramTreeFactory(root_node__year=self.current_working_year + 2)
        validator = MinimumMaximumPostponementYearValidator(tree_to_fill_in)
        self.assertFalse(validator.is_valid())
        expected_result = _("You are not allowed to postpone this training in the future.")
        self.assertListEqual([expected_result], validator.error_messages)

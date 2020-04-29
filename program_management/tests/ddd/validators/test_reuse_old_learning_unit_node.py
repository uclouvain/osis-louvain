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
import copy

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from program_management.ddd.validators._reuse_old_learning_unit_node import ReuseOldLearningUnitNodeValidator
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestReuseOldLearningUnitNodeValidatorValidator(SimpleTestCase):

    def setUp(self):
        self.year_of_tree_to_fill = 2020
        self.tree_to_fill = ProgramTreeFactory(root_node__year=self.year_of_tree_to_fill)

        same_root_last_year = copy.deepcopy(self.tree_to_fill.root_node)
        same_root_last_year.year -= 1
        same_program_last_year = ProgramTreeFactory(root_node=same_root_last_year)
        link = LinkFactory(parent=same_program_last_year.root_node)
        self.node_to_copy = link.child

    def test_when_existing_nodes_year_is_incorrect(self):
        incorrect_year = self.year_of_tree_to_fill - 10  # sth different from year of tree
        existing_nodes = [
            NodeLearningUnitYearFactory(year=incorrect_year),
            NodeLearningUnitYearFactory(year=incorrect_year),
        ]
        with self.assertRaises(AssertionError):
            "The year of existing nodes must be the same as the year of the tree to fill in content"
            ReuseOldLearningUnitNodeValidator(self.tree_to_fill, self.node_to_copy, existing_nodes)

    def test_when_existing_nodes_year_has_more_than_one_year(self):
        incorrect_year = self.year_of_tree_to_fill - 10
        existing_nodes = [
            NodeLearningUnitYearFactory(year=incorrect_year),
            NodeLearningUnitYearFactory(year=self.year_of_tree_to_fill),
        ]
        with self.assertRaises(AssertionError):
            "Should have only 1 year into the existing nodes"
            ReuseOldLearningUnitNodeValidator(self.tree_to_fill, self.node_to_copy, existing_nodes)

    def test_when_node_to_copy_exist_next_year(self):
        same_node_current_year = copy.deepcopy(self.node_to_copy)
        same_node_current_year.year = self.year_of_tree_to_fill
        existing_nodes = [same_node_current_year]
        validator = ReuseOldLearningUnitNodeValidator(self.tree_to_fill, self.node_to_copy, existing_nodes)
        self.assertTrue(validator.is_valid())
        self.assertListEqual([], validator.warning_messages)

    def test_when_node_to_copy_does_not_exist_on_year_of_tree_to_fill(self):
        existing_nodes = []
        validator = ReuseOldLearningUnitNodeValidator(self.tree_to_fill, self.node_to_copy, existing_nodes)
        self.assertTrue(validator.is_valid())
        expected_result = _("Learning unit %(learning_unit_year)s does not exist in %(academic_year)s => "
                            "Learning unit is postponed with academic year of %(learning_unit_academic_year)s.") % {
                              "learning_unit_year": self.node_to_copy.code,
                              "academic_year": self.tree_to_fill.root_node.year,
                              "learning_unit_academic_year": self.node_to_copy.academic_year
                          }
        self.assertListEqual([expected_result], validator.warning_messages)

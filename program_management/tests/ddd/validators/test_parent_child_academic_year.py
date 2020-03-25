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

from program_management.ddd.domain.program_tree import build_path
from program_management.ddd.validators._parent_child_academic_year import ParentChildSameAcademicYearValidator
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestParentChildSameAcademicYearValidator(SimpleTestCase):

    def setUp(self):
        self.year = 2019
        self.tree = ProgramTreeFactory(root_node__year=self.year)
        self.path_to_attach = build_path(self.tree.root_node)

    def test_when_year_equals(self):
        validator = ParentChildSameAcademicYearValidator(
            self.tree,
            NodeGroupYearFactory(year=self.year),
            self.path_to_attach
        )
        self.assertTrue(validator.is_valid())

    def test_when_year_of_node_to_attach_is_lower(self):
        validator = ParentChildSameAcademicYearValidator(
            self.tree,
            NodeGroupYearFactory(year=self.year - 1),
            self.path_to_attach
        )
        self.assertFalse(validator.is_valid())
        expected_result = _(
            "It is prohibited to attach a group, mini-training or training to an element of another academic year."
        )
        self.assertEqual(expected_result, validator.error_messages[0])

    def test_when_year_of_node_to_attach_is_greater(self):
        validator = ParentChildSameAcademicYearValidator(
            self.tree,
            NodeGroupYearFactory(year=self.year + 1),
            self.path_to_attach
        )
        self.assertFalse(validator.is_valid())
        expected_result = _(
            "It is prohibited to attach a group, mini-training or training to an element of another academic year."
        )
        self.assertEqual(expected_result, validator.error_messages[0])

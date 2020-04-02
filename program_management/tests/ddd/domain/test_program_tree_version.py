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
from mock import patch

from program_management.ddd.domain import program_tree_version
from program_management.ddd.domain.program_tree_version import ProgramTreeVersion, ProgramTreeVersionBuilder
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestInit(SimpleTestCase):
    def setUp(self):
        self.tree = ProgramTreeFactory()

    def test_default_version_name_value(self):
        obj = ProgramTreeVersion(self.tree)
        error_msg = "By default, a tree version instance is a 'Standard' version, identified by an empty name."
        self.assertEqual(obj.version_name, '', error_msg)

    def test_default_transition_value(self):
        obj = ProgramTreeVersion(self.tree)
        error_msg = "By default, a tree version instance is not a transition program."
        self.assertFalse(obj.is_transition, error_msg)


class TestBuilderBuildFrom(SimpleTestCase):

    def setUp(self):
        self.tree = ProgramTreeFactory()
        self.builder = ProgramTreeVersionBuilder()

    def test_when_tree_is_incorrect_type(self):
        with self.assertRaises(AssertionError):
            self.builder.build_from("bad arg")

    def test_when_tree_is_not_standard(self):
        tree = ProgramTreeVersion(self.tree, version_name="CEMS")
        with self.assertRaises(AssertionError):
            self.builder.build_from(tree)

    @patch.object(program_tree_version.ProgramTreeVersionBuilder, '_build_from_transition')
    @patch.object(program_tree_version.ProgramTreeVersionBuilder, '_build_from_standard')
    def test_when_tree_is_transition(self, mock_standard, mock_transition):
        tree = ProgramTreeVersion(self.tree, is_transition=True)
        self.builder.build_from(tree)
        self.assertTrue(mock_transition.called)
        self.assertFalse(mock_standard.called)

    @patch.object(program_tree_version.ProgramTreeVersionBuilder, '_build_from_transition')
    @patch.object(program_tree_version.ProgramTreeVersionBuilder, '_build_from_standard')
    def test_when_tree_is_not_transition(self, mock_standard, mock_transition):
        tree = ProgramTreeVersion(self.tree, is_transition=False)
        self.builder.build_from(tree)
        self.assertFalse(mock_transition.called)
        self.assertTrue(mock_standard.called)

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
import mock
from django.test import SimpleTestCase

from program_management.ddd.domain.exception import ProgramTreeNonEmpty
from program_management.ddd.validators._empty_program_tree import EmptyProgramTreeValidator
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestEmptyProgramTree(SimpleTestCase):
    def setUp(self) -> None:
        self.tree = ProgramTreeFactory()

    @mock.patch('program_management.ddd.domain.program_tree.ProgramTree.is_empty', return_value=False)
    def test_should_raise_exception_when_tree_is_not_empty(self, mock_is_empty):
        validator = EmptyProgramTreeValidator(self.tree)
        with self.assertRaises(ProgramTreeNonEmpty):
            validator.validate()

    @mock.patch('program_management.ddd.domain.program_tree.ProgramTree.is_empty', return_value=True)
    def test_should_not_raise_exception_when_tree_is_empty(self, mock_is_empty):
        validator = EmptyProgramTreeValidator(self.tree)
        validator.validate()
        self.assertTrue(mock_is_empty.called)

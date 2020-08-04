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
from django.test import TestCase

from program_management.ddd import command
from program_management.ddd.service.write import copy_program_tree_service
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestCopyProgramTreeToNextYear(TestCase):
    @mock.patch("program_management.ddd.service.write.copy_program_tree_service.ProgramTreeRepository")
    @mock.patch("program_management.ddd.domain.program_tree.ProgramTreeBuilder.copy_to_next_year")
    def test_should_create_next_year_program_tree_and_persist_it(self, mock_copy_to_next_year, mock_repository):
        program_tree = ProgramTreeFactory()
        next_year_program_tree = ProgramTreeFactory()

        mock_copy_to_next_year.return_value = next_year_program_tree
        mock_repository.get.return_value = program_tree
        mock_repository.return_value.create.return_value = next_year_program_tree.entity_id

        cmd = command.CopyProgramTreeToNextYearCommand(code="Code", year=2020)
        result = copy_program_tree_service.copy_program_tree_to_next_year(cmd)

        self.assertEqual(next_year_program_tree.entity_id, result)

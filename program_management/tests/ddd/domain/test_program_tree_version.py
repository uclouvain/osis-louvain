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
import attr
import mock
from django.test import SimpleTestCase

from program_management.ddd.domain import program_tree_version
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory


class TestProgramTreeVersionBuilderCopyToNextYear(SimpleTestCase):
    def setUp(self):
        self.copy_from_program_tree_version = ProgramTreeVersionFactory()
        self.mock_repository = mock.create_autospec(ProgramTreeVersionRepository)

    def test_should_create_new_tree_version_when_does_not_exist_for_next_year(self):
        self.mock_repository.get.return_value = None

        result_tree_version = program_tree_version.ProgramTreeVersionBuilder().copy_to_next_year(
            self.copy_from_program_tree_version,
            self.mock_repository
        )

        expected_tree_identity = attr.evolve(
            self.copy_from_program_tree_version.program_tree_identity,
            year=self.copy_from_program_tree_version.program_tree_identity.year + 1
        )
        self.assertEqual(expected_tree_identity, result_tree_version.program_tree_identity)

    def test_should_return_existing_tree_version_when_already_exists_for_next_year(self):
        next_year_program_tree_version = ProgramTreeVersionFactory()
        self.mock_repository.get.return_value = next_year_program_tree_version

        result_tree_version = program_tree_version.ProgramTreeVersionBuilder().copy_to_next_year(
            self.copy_from_program_tree_version,
            self.mock_repository
        )

        self.assertEqual(next_year_program_tree_version, result_tree_version)

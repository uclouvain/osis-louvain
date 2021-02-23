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
from django.test import TestCase

from base.tests.factories.academic_year import AcademicYearFactory
from program_management.ddd.command import DeleteSpecificVersionCommand
from program_management.ddd.service.write import update_program_tree_version_service
from program_management.tests.ddd.factories.commands.update_program_tree_version import \
    UpdateProgramTreeVersionCommandFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from program_management.tests.ddd.factories.repository.fake import get_fake_program_tree_version_repository
from testing.mocks import MockPatcherMixin


@mock.patch("program_management.ddd.service.write.delete_specific_version_service.delete_specific_version")
class TestUpdateTrainingVersion(TestCase, MockPatcherMixin):

    @classmethod
    def setUpTestData(cls):
        AcademicYearFactory.produce_in_future()
        cls.current_year = AcademicYearFactory(current=True).year
        cls.end_year_of_existence = cls.current_year + 5
        cls.tree_version = ProgramTreeVersionFactory(
            entity_id__year=cls.current_year,
            end_year_of_existence=cls.end_year_of_existence,
        )
        cls.command = UpdateProgramTreeVersionCommandFactory(
            version_name=cls.tree_version.entity_id.version_name,
            year=cls.tree_version.entity_id.year,
            offer_acronym=cls.tree_version.entity_id.offer_acronym,
            transition_name=cls.tree_version.entity_id.transition_name,
            end_year=cls.tree_version.end_year_of_existence,
            title_fr="another title",
            title_en="another title in english"
        )

    def setUp(self):
        self.fake_program_tree_version_repository = get_fake_program_tree_version_repository([self.tree_version])
        self.mock_repo(
            "program_management.ddd.service.write.update_program_tree_version_service.ProgramTreeVersionRepository",
            self.fake_program_tree_version_repository
        )

    def test_when_end_year_is_none(self, mock_delete_tree_version_service):
        new_end_year = None  # Equivalent to max_year == N + 6
        cmd = attr.evolve(self.command, end_year=new_end_year)
        result = update_program_tree_version_service.update_program_tree_version(cmd)
        updated_entity = self.fake_program_tree_version_repository.get(result)
        self.assertFalse(mock_delete_tree_version_service.called)
        self.assertIsNone(updated_entity.end_year_of_existence)

    def test_when_end_year_is_lower(self, mock_delete_tree_version_service):
        new_end_year = self.tree_version.end_year_of_existence - 2
        cmd = attr.evolve(self.command, end_year=new_end_year)
        result = update_program_tree_version_service.update_program_tree_version(cmd)
        updated_entity = self.fake_program_tree_version_repository.get(result)
        self.assertTrue(mock_delete_tree_version_service.called)
        self.assertEqual(updated_entity.end_year_of_existence, new_end_year)

    def test_assert_delete_tree_version_called_right_number(self, mock_delete_tree_version_service):
        new_end_year = self.tree_version.end_year_of_existence - 3
        cmd = attr.evolve(self.command, end_year=new_end_year)
        update_program_tree_version_service.update_program_tree_version(cmd)

        calls = [
            mock.call(
                DeleteSpecificVersionCommand(
                    acronym=self.tree_version.entity_id.offer_acronym,
                    year=self.current_year + 3,
                    version_name=self.tree_version.entity_id.version_name,
                    transition_name=self.tree_version.entity_id.transition_name,
                )
            ),
            mock.call(
                DeleteSpecificVersionCommand(
                    acronym=self.tree_version.entity_id.offer_acronym,
                    year=self.current_year + 4,
                    version_name=self.tree_version.entity_id.version_name,
                    transition_name=self.tree_version.entity_id.transition_name,
                )
            )
        ]
        mock_delete_tree_version_service.assert_has_calls(calls)

    def test_updated_values(self, mock_delete_tree_version_service):
        result = update_program_tree_version_service.update_program_tree_version(self.command)
        self.assertEqual(result, self.tree_version.entity_id)
        updated_entity = self.fake_program_tree_version_repository.get(result)
        self.assertEqual(updated_entity.title_fr, self.command.title_fr)
        self.assertEqual(updated_entity.title_en, self.command.title_en)
        self.assertEqual(updated_entity.end_year_of_existence, self.command.end_year)
        self.assertFalse(mock_delete_tree_version_service.called)

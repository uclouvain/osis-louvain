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

from education_group.tests.factories.group import GroupFactory
from program_management.ddd import command
from program_management.ddd.service.write import create_standard_program_tree_service
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestCreateStandardProgramTree(TestCase):
    @mock.patch("program_management.ddd.service.write.create_standard_program_tree_service.GroupRepository")
    @mock.patch("program_management.ddd.service.write.create_standard_program_tree_service.ProgramTreeBuilder")
    @mock.patch("program_management.ddd.service.write.create_standard_program_tree_service.ProgramTreeRepository")
    def test_should_create_standard_program_tree_and_persist_it(
            self,
            mock_tree_repository,
            mock_tree_builder,
            mock_group_repostory):
        standard_program_tree = ProgramTreeFactory()
        mock_group_repostory.return_value.get.return_value = GroupFactory()
        mock_tree_builder.return_value.build_from_orphan_group_as_root.return_value = standard_program_tree
        mock_tree_repository.return_value.create.return_value = standard_program_tree.entity_id

        cmd = command.CreateStandardVersionCommand(offer_acronym="Offer", code="Code", year=2025)
        result = create_standard_program_tree_service.create_standard_program_tree(cmd)

        self.assertEqual(standard_program_tree.entity_id, result)

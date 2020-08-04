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
from program_management.ddd.service.write import create_standard_version_service
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory


class TestCreateStandardProgramVersion(TestCase):
    @mock.patch("program_management.ddd.service.write.create_standard_version_service.ProgramTreeVersionBuilder")
    @mock.patch("program_management.ddd.service.write.create_standard_version_service.ProgramTreeVersionRepository")
    def test_create_program_tree_version_and_persist_it(
            self,
            mock_version_repository,
            mock_version_builder):
        standard_program_version = ProgramTreeVersionFactory()
        mock_version_builder.return_value.build_standard_version.return_value = standard_program_version
        mock_version_repository.return_value.create.return_value = standard_program_version.entity_id

        cmd = command.CreateStandardVersionCommand(offer_acronym="Offer", code="Code", year=2018)
        result = create_standard_version_service.create_standard_program_version(cmd)

        self.assertEqual(standard_program_version.entity_id, result)

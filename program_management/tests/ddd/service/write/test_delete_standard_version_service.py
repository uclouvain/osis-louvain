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
from unittest import mock

from django.test import TestCase

from program_management.ddd import command
from program_management.ddd.service.write import delete_standard_version_service
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory


class TestDeleteStandardVersionService(TestCase):
    def setUp(self):
        self.tree_version = ProgramTreeVersionFactory()
        self.parent = self.tree_version.tree.root_node
        self.link1 = LinkFactory(parent=self.parent, child=NodeGroupYearFactory(), order=0)

        self.get_tree_patcher = mock.patch(
            "program_management.ddd.service.write.delete_standard_version_service.ProgramTreeVersionRepository.get",
            return_value=self.tree_version
        )
        self.mocked_get_tree = self.get_tree_patcher.start()
        self.addCleanup(self.get_tree_patcher.stop)

        self.delete_tree_patcher = mock.patch(
            "program_management.ddd.service.write.delete_standard_version_service.ProgramTreeVersionRepository.delete",
            return_value=None
        )
        self.mocked_delete_tree = self.delete_tree_patcher.start()
        self.addCleanup(self.delete_tree_patcher.stop)

    @mock.patch('program_management.ddd.service.write.delete_standard_version_service.'
                'DeleteStandardVersionValidatorList')
    def test_assert_delete_program_tree_validator_called(self, mock_validator):
        cmd = command.DeleteStandardVersionCommand(acronym="Dummy", year=2018)
        delete_standard_version_service.delete_standard_version(cmd)

        self.assertTrue(mock_validator.called)

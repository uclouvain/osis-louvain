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

from django.test import SimpleTestCase

from program_management.ddd import command
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.read import get_program_tree_version_from_node_service


class TestGetProgramTreeVersionFromNodeService(SimpleTestCase):

    @mock.patch.object(ProgramTreeVersionIdentitySearch, 'get_from_node_identity')
    @mock.patch.object(ProgramTreeVersionRepository, 'get')
    def test_domain_service_is_called(self, mock_domain_service, mock_repository_get):
        cmd = command.GetProgramTreeVersionFromNodeCommand(code="LDROI1200", year=2018)
        get_program_tree_version_from_node_service.get_program_tree_version_from_node(cmd)
        self.assertTrue(mock_domain_service.called)
        self.assertTrue(mock_repository_get.called)

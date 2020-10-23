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
from imp import reload
from unittest import mock

from django.test import SimpleTestCase
from mock import patch

import program_management.ddd.service.write.bulk_update_link_service
from program_management.ddd.command import BulkUpdateLinkCommand
from program_management.ddd.service.write import update_link_service, bulk_update_link_service
from program_management.tests.ddd.factories.commands.update_link_comand import UpdateLinkCommandFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


def mock_decorator(f):
    def decorated_function(g):
        return g
    return decorated_function(f)


class TestBulkUpdateLink(SimpleTestCase):

    def setUp(self):
        self.tree = ProgramTreeFactory()
        self.parent = self.tree.root_node
        self.link = LinkFactory(parent=self.parent, child=NodeLearningUnitYearFactory())
        self.mock_atomic_transaction = patch(
            "program_management.ddd.service.write.bulk_update_link_service.transaction.atomic",
            return_value=mock_decorator
        )
        self.mock_atomic_transaction_patcher = self.mock_atomic_transaction.start()
        self.addCleanup(self.mock_atomic_transaction.stop)

    @patch('program_management.ddd.repositories.program_tree.ProgramTreeRepository.get')
    @patch('program_management.ddd.domain.program_tree.ProgramTree.update_link')
    @patch('program_management.ddd.repositories.program_tree.ProgramTreeRepository.update')
    def test_should_call_tree_update_link_for_bulk_update(self, mock_update_tree, mock_update_link, mock_get_tree):
        mock_get_tree.return_value = self.tree
        # reload update_link_service to apply mock decorator
        reload(bulk_update_link_service)
        command = BulkUpdateLinkCommand(
            parent_node_code=self.parent.code, parent_node_year=self.parent.year,
            update_link_cmds=[UpdateLinkCommandFactory() for _ in range(0, 2)]
        )
        bulk_update_link_service.bulk_update_links(cmd=command)
        self.assertTrue(mock_update_link.called)
        self.assertTrue(mock_update_tree.called)

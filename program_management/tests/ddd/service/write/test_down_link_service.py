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

from django.test import SimpleTestCase, TestCase

from program_management.ddd.domain import program_tree, link, node
from program_management.ddd.service.write import down_link_service
from program_management.tests.ddd.factories.commands.order_down_link_command import OrderDownLinkCommandFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestDownLink(TestCase):

    def setUp(self):
        self.tree = ProgramTreeFactory()
        self.parent = self.tree.root_node
        self.link0 = LinkFactory(parent=self.parent, child=NodeLearningUnitYearFactory(), order=0)
        self.link1 = LinkFactory(parent=self.parent, child=NodeGroupYearFactory(), order=1)
        self.link2 = LinkFactory(parent=self.parent, child=NodeLearningUnitYearFactory(), order=2)

        self.load_tree_patcher = mock.patch(
            "program_management.ddd.repositories.load_tree.load",
            return_value=self.tree
        )
        self.mocked_load_tree = self.load_tree_patcher.start()
        self.addCleanup(self.load_tree_patcher.stop)

        self.persist_tree_patcher = mock.patch(
            "program_management.ddd.repositories.persist_tree.persist",
            return_value=None
        )
        self.mocked_persist_tree = self.persist_tree_patcher.start()
        self.addCleanup(self.persist_tree_patcher.stop)

        self.load_node_element = mock.patch(
            "program_management.ddd.repositories.load_node.load",
        )
        self.mocked_load_node_element = self.load_node_element.start()
        self.addCleanup(self.load_node_element.stop)

    def test_should_return_node_identity_of_node_downed(self):
        self.mocked_load_node_element.side_effect = [self.parent, self.link1.child]

        command = OrderDownLinkCommandFactory(path=program_tree.build_path(self.parent, self.link1.child))
        result = down_link_service.down_link(command)
        expected = node.NodeIdentity(
            code=self.link1.child.code,
            year=self.link1.child.academic_year.year
        )
        self.assertEqual(
            result,
            expected
        )

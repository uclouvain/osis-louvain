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

from program_management.ddd.command import OrderUpLinkCommand
from program_management.ddd.domain import program_tree
from program_management.ddd.service.write import up_link_service
from program_management.tests.ddd.factories.domain.program_tree_version.training.OSIS1BA import OSIS1BAFactory
from testing.testcases import DDDTestCase


class TestUpLinkService(DDDTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tree = OSIS1BAFactory()[0].tree
        self.cmd = OrderUpLinkCommand(
            path=program_tree.build_path(self.tree.root_node, self.tree.root_node.children_as_nodes[1])
        )

    def test_should_replace_one_child_before(self):
        node_id = up_link_service.up_link(self.cmd)

        children = self.tree.root_node.children_as_nodes
        self.assertEqual(node_id, children[0].entity_id)

    def test_should_keep_order_when_child_is_already_the_first_child(self):
        cmd = attr.evolve(
            self.cmd,
            path=program_tree.build_path(self.tree.root_node, self.tree.root_node.children_as_nodes[0])
        )
        order_before_service_call = self.tree.root_node.children_as_nodes

        up_link_service.up_link(cmd)

        order_after_service_call = self.tree.root_node.children_as_nodes
        self.assertListEqual(order_before_service_call, order_after_service_call)

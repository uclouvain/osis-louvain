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

from program_management.ddd.service import order_link_service
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestUpDownChildren(SimpleTestCase):

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

        self.load_node_education_group_year_patcher = mock.patch(
            "program_management.ddd.repositories.load_node.load_node_education_group_year",
            return_value=self.parent
        )
        self.mocked_load_node_education_group_year = self.load_node_education_group_year_patcher.start()
        self.addCleanup(self.mocked_load_node_education_group_year.stop)

    @mock.patch("program_management.ddd.repositories.load_node.load_by_type")
    def test_do_not_modify_order_when_applying_up_on_first_element(self, mock_load_child):
        mock_load_child.return_value = self.link0.child
        order_link_service.up_link(
            self.parent.node_id,
            self.link0.parent.node_id,
            self.link0.child.node_id,
            self.link0.child.type
        )
        self.assertListEqual(
            self.parent.children,
            [self.link0, self.link1, self.link2]
        )
        self.assertFalse(self.mocked_persist_tree.called)

    @mock.patch("program_management.ddd.repositories.load_node.load_by_type")
    def test_up_action_on_link_should_increase_order_by_one(self, mock_load_child):
        mock_load_child.return_value = self.link1.child
        order_link_service.up_link(
            self.parent.node_id,
            self.link1.parent.node_id,
            self.link1.child.node_id,
            self.link1.child.type
        )
        self.assertListEqual(
            [self.link1.order, self.link0.order, self.link2.order],
            [0, 1, 2]
        )
        self.assertTrue(self.mocked_persist_tree.called)

    @mock.patch("program_management.ddd.repositories.load_node.load_by_type")
    def test_down_action_on_link_should_decrease_order_by_one(self, mock_load_child):
        mock_load_child.return_value = self.link1.child
        order_link_service.down_link(
            self.parent.node_id,
            self.link1.parent.node_id,
            self.link1.child.node_id,
            self.link1.child.type
        )
        self.assertListEqual(
            [self.link0.order, self.link2.order, self.link1.order],
            [0, 1, 2]
        )
        self.assertTrue(self.mocked_persist_tree.called)

    @mock.patch("program_management.ddd.repositories.load_node.load_by_type")
    def test_do_not_modify_order_when_applying_down_on_last_element(self, mock_load_child):
        mock_load_child.return_value = self.link2.child
        order_link_service.down_link(
            self.parent.node_id,
            self.link2.parent.node_id,
            self.link2.child.node_id,
            self.link2.child.type
        )
        self.assertListEqual(
            self.parent.children,
            [self.link0, self.link1, self.link2]
        )
        self.assertFalse(self.mocked_persist_tree.called)

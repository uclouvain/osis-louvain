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

from base.models.enums.link_type import LinkTypes
from program_management.ddd.command import BulkUpdateLinkCommand, UpdateLinkCommand
from program_management.ddd.domain.exception import BulkUpdateLinkException
from program_management.ddd.domain.link import LinkIdentity
from program_management.ddd.service.write import bulk_update_link_service
from program_management.tests.ddd.factories.domain.program_tree_version.training.OSIS1BA import OSIS1BAFactory
from testing.testcases import DDDTestCase


class TestBulkUpdateLink(DDDTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tree = OSIS1BAFactory()[0].tree
        self.cmd = BulkUpdateLinkCommand(
            parent_node_code=self.tree.root_node.code,
            parent_node_year=self.tree.root_node.year,
            update_link_cmds=[
                UpdateLinkCommand(
                    block="123",
                    parent_node_code=self.tree.root_node.code,
                    parent_node_year=self.tree.root_node.year,
                    child_node_code=self.tree.root_node.children_as_nodes[0].code,
                    child_node_year=self.tree.root_node.children_as_nodes[0].year,
                    link_type=None,
                    comment="A comment",
                    comment_english="A comment in english",
                    relative_credits=20,
                    is_mandatory=False,
                    access_condition=False
                ),
                UpdateLinkCommand(
                    block=None,
                    parent_node_code=self.tree.root_node.code,
                    parent_node_year=self.tree.root_node.year,
                    child_node_code=self.tree.root_node.children_as_nodes[1].code,
                    child_node_year=self.tree.root_node.children_as_nodes[1].year,
                    link_type=None,
                    comment="Another update",
                    comment_english="ANother update",
                    relative_credits=20,
                    is_mandatory=False,
                    access_condition=False
                )
            ]
        )

    def test_should_return_link_updated(self):
        result = bulk_update_link_service.bulk_update_links(self.cmd)

        expected = [
            LinkIdentity(
                parent_code=self.tree.root_node.code,
                child_code=self.tree.root_node.children_as_nodes[1].code,
                parent_year=self.tree.root_node.year,
                child_year=self.tree.root_node.children_as_nodes[1].year
            ),
            LinkIdentity(
                parent_code=self.tree.root_node.code,
                child_code=self.tree.root_node.children_as_nodes[0].code,
                parent_year=self.tree.root_node.year,
                child_year=self.tree.root_node.children_as_nodes[0].year
            )
        ]
        actual_identities = [link.entity_id for link in result]
        self.assertCountEqual(expected, actual_identities)

    def test_should_aggregate_each_update_link_errors_into_one(self):
        cmd = attr.evolve(
            self.cmd,
            update_link_cmds=[
                attr.evolve(self.cmd.update_link_cmds[0], block="159"),
                attr.evolve(self.cmd.update_link_cmds[1], link_type=LinkTypes.REFERENCE.name)
            ]
        )

        with self.assertRaisesBusinessException(BulkUpdateLinkException) as e:
            bulk_update_link_service.bulk_update_links(cmd)

        exceptions = e.exception.exceptions
        self.assertTrue(len(exceptions) > 1)

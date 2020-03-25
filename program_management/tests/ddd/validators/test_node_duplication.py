##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from program_management.ddd.domain.program_tree import build_path
from program_management.ddd.validators._node_duplication import NodeDuplicationValidator
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestNodeDuplicationValidator(SimpleTestCase):

    def setUp(self):
        link = LinkFactory()
        self.tree_with_child = ProgramTreeFactory(root_node=link.parent)
        self.child = link.child

    def test_when_node_already_exists(self):
        node_to_attach = self.child
        validator = NodeDuplicationValidator(
            self.tree_with_child,
            node_to_attach,
            build_path(self.tree_with_child.root_node)
        )
        self.assertFalse(validator.is_valid())
        expected_result = _("You can not add the same child several times.")
        self.assertEqual(expected_result, validator.error_messages[0])

    def test_when_node_already_exists_in_other_group_of_the_same_tree(self):
        node_to_attach = NodeGroupYearFactory()
        link = LinkFactory(parent=self.tree_with_child.root_node)
        LinkFactory(parent=link.child, child=node_to_attach)
        validator = NodeDuplicationValidator(
            self.tree_with_child,
            node_to_attach,
            build_path(self.tree_with_child.root_node)
        )
        self.assertTrue(validator.is_valid())

    def test_when_node_does_not_exists(self):
        node_to_attach = NodeGroupYearFactory()
        validator = NodeDuplicationValidator(
            self.tree_with_child,
            node_to_attach,
            build_path(self.tree_with_child.root_node)
        )
        self.assertTrue(validator.is_valid())

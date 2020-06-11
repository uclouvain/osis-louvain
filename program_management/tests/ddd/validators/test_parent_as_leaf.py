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

from program_management.ddd.validators._parent_as_leaf import ParentIsNotLeafValidator
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestParentIsNotLeafValidator(SimpleTestCase):

    def setUp(self):
        link = LinkFactory(child=NodeLearningUnitYearFactory())
        self.tree_with_child = ProgramTreeFactory(root_node=link.parent)
        self.child = link.child

    def test_when_trying_to_add_node_to_leaf(self):
        validator = ParentIsNotLeafValidator(
            self.child,
            NodeGroupYearFactory()
        )
        self.assertFalse(validator.is_valid())
        expected_result = _("Cannot add any element to learning unit %(parent_node)s") % {
            "parent_node": self.child
        }
        self.assertEqual(expected_result, validator.error_messages[0])

    def test_when_trying_to_add_leaf_to_leaf(self):
        validator = ParentIsNotLeafValidator(
            self.child,
            NodeLearningUnitYearFactory()
        )
        self.assertFalse(validator.is_valid())
        expected_result = _("Cannot add any element to learning unit %(parent_node)s") % {
            "parent_node": self.child
        }
        self.assertEqual(expected_result, validator.error_messages[0])

    def test_when_trying_to_add_leaf_to_group(self):
        validator = ParentIsNotLeafValidator(
            self.tree_with_child.root_node,
            NodeLearningUnitYearFactory()
        )
        self.assertTrue(validator.is_valid())

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

from base.models.authorized_relationship import AuthorizedRelationshipList
from base.models.enums.education_group_types import TrainingType, GroupType
from base.tests.factories.academic_year import AcademicYearFactory
from program_management.ddd.validators._authorized_relationship import AttachAuthorizedRelationshipValidator, \
    DetachAuthorizedRelationshipValidator
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestAttachAuthorizedRelationshipValidator(SimpleTestCase):

    def setUp(self):
        self.academic_year = AcademicYearFactory.build(current=True)

        self.authorized_parent = NodeGroupYearFactory(
            node_type=TrainingType.BACHELOR,
            year=self.academic_year.year,
        )
        self.authorized_child = NodeGroupYearFactory(
            node_type=GroupType.COMMON_CORE,
            year=self.academic_year.year,
        )
        self.authorized_relationships = AuthorizedRelationshipList([
            AuthorizedRelationshipFactory(
                parent_type=self.authorized_parent.node_type,
                child_type=self.authorized_child.node_type,
                max_constraint=1,
            )
        ])
        self.tree = ProgramTreeFactory(
            root_node=self.authorized_parent,
            authorized_relationships=self.authorized_relationships
        )

    def test_success(self):
        tree = ProgramTreeFactory(
            root_node=NodeGroupYearFactory(node_type=TrainingType.BACHELOR),
            authorized_relationships=self.authorized_relationships
        )
        validator = AttachAuthorizedRelationshipValidator(tree, self.authorized_child, tree.root_node)
        result = validator.is_valid()
        self.assertTrue(result)

    def test_when_relation_is_not_authorized(self):
        unauthorized_child = NodeGroupYearFactory(node_type=GroupType.COMPLEMENTARY_MODULE)
        validator = AttachAuthorizedRelationshipValidator(self.tree, unauthorized_child, self.authorized_parent)
        self.assertFalse(validator.is_valid())
        error_msg = _("You cannot add \"%(child_types)s\" to \"%(parent)s\" (type \"%(parent_type)s\")") % {
            'child_types': unauthorized_child.node_type.value,
            'parent': self.authorized_parent,
            'parent_type': self.authorized_parent.node_type.value,
        }

        self.assertIn(error_msg, validator.error_messages)

    def test_when_parent_has_no_children_yet(self):
        another_authorized_parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        self.assertEqual([], another_authorized_parent.children)
        tree = ProgramTreeFactory(
            root_node=another_authorized_parent,
            authorized_relationships=self.authorized_relationships
        )
        validator = AttachAuthorizedRelationshipValidator(tree, self.authorized_child, another_authorized_parent)
        self.assertTrue(validator.is_valid())

    def test_when_parent_has_children_but_maximum_is_not_reached(self):
        another_authorized_child = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP)
        another_authorized_parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        another_authorized_parent.add_child(another_authorized_child)  # add child manually, bypass validations
        tree = ProgramTreeFactory(
            root_node=another_authorized_parent,
            authorized_relationships=self.authorized_relationships
        )
        validator = AttachAuthorizedRelationshipValidator(tree, self.authorized_child, another_authorized_parent)
        self.assertTrue(validator.is_valid())

    def test_when_maximum_is_reached(self):
        self.authorized_parent.add_child(self.authorized_child)
        another_authorized_child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        validator = AttachAuthorizedRelationshipValidator(self.tree, another_authorized_child, self.authorized_parent)

        self.assertFalse(validator.is_valid())

        max_error_msg = _("The parent must have at least one child of type(s) \"%(types)s\".") % {
            "types": str(self.tree.authorized_relationships.get_authorized_children_types(self.authorized_parent.node_type))
        }
        self.assertIn(max_error_msg, validator.error_messages)
        self.assertEqual(len(validator.error_messages), 1)


class TestDetachAuthorizedRelationshipValidator(SimpleTestCase):

    def setUp(self):
        self.academic_year = AcademicYearFactory.build(current=True)

        self.authorized_parent = NodeGroupYearFactory(
            node_type=TrainingType.BACHELOR,
            year=self.academic_year.year,
        )
        self.authorized_child = NodeGroupYearFactory(
            node_type=GroupType.COMMON_CORE,
            year=self.academic_year.year,
        )
        self.authorized_relationships = AuthorizedRelationshipList([
            AuthorizedRelationshipFactory(
                parent_type=self.authorized_parent.node_type,
                child_type=self.authorized_child.node_type,
                min_constraint=1,
            )
        ])
        self.tree = ProgramTreeFactory(
            root_node=self.authorized_parent,
            authorized_relationships=self.authorized_relationships
        )

    def test_success(self):
        validator = DetachAuthorizedRelationshipValidator(self.tree, self.authorized_child, self.authorized_parent)
        self.assertTrue(validator.is_valid())

    def test_when_relation_is_not_authorized(self):
        unauthorized_child = NodeGroupYearFactory(node_type=GroupType.COMPLEMENTARY_MODULE)
        validator = DetachAuthorizedRelationshipValidator(self.tree, unauthorized_child, self.authorized_parent)
        self.assertTrue(validator.is_valid())

    def test_when_parent_has_no_children_yet(self):
        another_authorized_parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        self.assertEqual([], another_authorized_parent.children)
        tree = ProgramTreeFactory(
            root_node=another_authorized_parent,
            authorized_relationships=self.authorized_relationships
        )
        validator = DetachAuthorizedRelationshipValidator(tree, self.authorized_child, another_authorized_parent)
        self.assertTrue(validator.is_valid())

    def test_when_parent_has_children_but_minimum_is_not_reached(self):
        another_authorized_child = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP)
        another_authorized_parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        another_authorized_parent.add_child(another_authorized_child)
        tree = ProgramTreeFactory(
            root_node=another_authorized_parent,
            authorized_relationships=self.authorized_relationships
        )
        validator = DetachAuthorizedRelationshipValidator(tree, another_authorized_child, another_authorized_parent)
        self.assertTrue(validator.is_valid())

    def test_when_minimum_is_reached(self):
        self.authorized_parent.add_child(self.authorized_child)
        another_authorized_child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        validator = DetachAuthorizedRelationshipValidator(self.tree, another_authorized_child, self.authorized_parent)
        self.assertFalse(validator.is_valid())
        error_msg = _("The number of children of type(s) \"%(child_types)s\" for \"%(parent)s\" "
                      "has already reached the limit.") % {
                        'child_types': self.authorized_child.node_type.value,
                        'parent': self.authorized_parent
                    }
        self.assertIn(error_msg, validator.error_messages)

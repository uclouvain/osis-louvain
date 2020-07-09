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
from base.models.enums.link_type import LinkTypes
from base.tests.factories.academic_year import AcademicYearFactory
from program_management.ddd.validators._authorized_relationship import AttachAuthorizedRelationshipValidator, \
    DetachAuthorizedRelationshipValidator, AuthorizedRelationshipLearningUnitValidator
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipObjectFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
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
            AuthorizedRelationshipObjectFactory(
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
        error_msg = _("You cannot add \"%(child)s\" of type \"%(child_types)s\" "
                      "to \"%(parent)s\" of type \"%(parent_type)s\"") % {
            'child': unauthorized_child,
            'child_types': unauthorized_child.node_type.value,
            'parent': self.authorized_parent,
            'parent_type': self.authorized_parent.node_type.value
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

        max_error_msg = _(
            "Cannot add \"%(child)s\" because the number of children of type(s) \"%(child_types)s\" "
            "for \"%(parent)s\" has already reached the limit.") % {
            'child': another_authorized_child,
            'child_types': another_authorized_child.node_type.value,
            'parent': self.authorized_parent
        }

        self.assertIn(max_error_msg, validator.error_messages)
        self.assertEqual(len(validator.error_messages), 1)


class TestAuthorizedRelationshipLearningUnitValidator(SimpleTestCase):
    def test_when_parent_node_do_not_allow_learning_unit_as_children_should_be_not_valid(self):
        root_node = NodeGroupYearFactory()
        authorized_relationships = AuthorizedRelationshipList([
            AuthorizedRelationshipObjectFactory(
                parent_type=root_node.node_type,
                child_type=root_node.node_type,
            )
        ])
        tree = ProgramTreeFactory(root_node=root_node, authorized_relationships=authorized_relationships)
        node_to_add = NodeLearningUnitYearFactory()
        validator = AuthorizedRelationshipLearningUnitValidator(tree, node_to_add, tree.root_node)

        self.assertFalse(validator.is_valid())

        error_msg_expected = _("You can not attach a learning unit like %(node)s "
                               "to element %(parent)s of type %(type)s.") % {
            "node": node_to_add,
            "parent": tree.root_node,
            "type": tree.root_node.node_type.value
        }
        self.assertIn(error_msg_expected, validator.error_messages)

    def test_when_parent_node_allows_learning_unit_as_children_then_should_be_valid(self):
        root_node = NodeGroupYearFactory()
        authorized_relationships = AuthorizedRelationshipList([
            AuthorizedRelationshipObjectFactory(
                parent_type=root_node.node_type,
                child_type=NodeType.LEARNING_UNIT,
            )
        ])
        tree = ProgramTreeFactory(root_node=root_node, authorized_relationships=authorized_relationships)
        node_to_add = NodeLearningUnitYearFactory()
        validator = AuthorizedRelationshipLearningUnitValidator(tree, node_to_add, tree.root_node)

        self.assertTrue(validator.is_valid())


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
            AuthorizedRelationshipObjectFactory(
                parent_type=self.authorized_parent.node_type,
                child_type=self.authorized_child.node_type,
                min_constraint=1,
            ),
            AuthorizedRelationshipObjectFactory(
                parent_type=self.authorized_child.node_type,
                child_type=GroupType.SUB_GROUP,
                min_constraint=1,
            ),
            AuthorizedRelationshipObjectFactory(
                parent_type=self.authorized_child.node_type,
                child_type=NodeType.LEARNING_UNIT,
                min_constraint=1,
            ),
        ])
        self.tree = ProgramTreeFactory(
            root_node=self.authorized_parent,
            authorized_relationships=self.authorized_relationships
        )

    def test_success(self):
        LinkFactory(parent=self.authorized_parent, child=self.authorized_child)
        link = LinkFactory(parent=self.authorized_parent, child__node_type=GroupType.COMMON_CORE)
        validator = DetachAuthorizedRelationshipValidator(self.tree, link.child, self.authorized_parent)
        self.assertTrue(validator.is_valid())

    def test_when_relation_is_not_authorized(self):
        """
            Business case to fix :
            MINOR_LIST_CHOICE
               |--ACCESS_MINOR (link_type=reference)
                  |--COMMON_CORE
            # FIXME :: What if we want to detach ACCESS_MINOR in the tree above?
            # FIXME :: In this case, the relation between child of minor () COMMON_CORE and parent of minor (MINOR_LIST_CHOICE) is not authorized.
            # FIXME :: While this test pass, it permit to ignore validation if the authorized_relationship does not exist.
        """
        unauthorized_child = NodeGroupYearFactory(node_type=GroupType.COMPLEMENTARY_MODULE)
        LinkFactory(parent=self.authorized_parent, child=unauthorized_child)
        validator = DetachAuthorizedRelationshipValidator(self.tree, unauthorized_child, self.authorized_parent)
        self.assertTrue(validator.is_valid())

    def test_when_parent_has_children_but_minimum_is_not_reached(self):
        another_authorized_child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        another_authorized_parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        another_authorized_parent.add_child(another_authorized_child)
        another_authorized_parent.add_child(self.authorized_child)
        tree = ProgramTreeFactory(
            root_node=another_authorized_parent,
            authorized_relationships=self.authorized_relationships
        )
        validator = DetachAuthorizedRelationshipValidator(tree, another_authorized_child, another_authorized_parent)
        self.assertTrue(validator.is_valid())

    def test_when_minimum_is_reached(self):
        node_to_detach = self.authorized_child
        detach_from = self.authorized_parent
        LinkFactory(parent=detach_from, child=node_to_detach)
        validator = DetachAuthorizedRelationshipValidator(self.tree, node_to_detach, detach_from)
        self.assertFalse(validator.is_valid())
        expected_error_msg = _("The parent must have at least one child of type(s) \"%(types)s\".") % {
            "types": str(node_to_detach.node_type.value)
        }
        self.assertListEqual([expected_error_msg], validator.error_messages)

    def test_when_link_to_detach_is_reference(self):
        """
        BACHELOR
           |--COMMON_CORE
              |--LEARNING_UNIT
        """
        LinkFactory(parent=self.authorized_parent, child=self.authorized_child)
        link = LinkFactory(parent=self.authorized_child, child__node_type=NodeType.LEARNING_UNIT)

        node_to_detach = link.child
        detach_from = link.parent
        validator = DetachAuthorizedRelationshipValidator(self.tree, node_to_detach, detach_from)

        self.assertFalse(validator.is_valid())
        expected_error_msg = _("The parent must have at least one child of type(s) \"%(types)s\".") % {
            "types": str(NodeType.LEARNING_UNIT.value)
        }
        self.assertListEqual([expected_error_msg], validator.error_messages)

    def test_when_link_to_detach_is_learning_unit(self):
        LinkFactory(parent=self.authorized_parent, child=self.authorized_child)
        reference_link = LinkFactory(
            parent=self.authorized_child,
            child__node_type=self.authorized_child.node_type,
            link_type=LinkTypes.REFERENCE
        )
        child_type_under_reference = GroupType.SUB_GROUP
        LinkFactory(parent=reference_link.child, child__node_type=child_type_under_reference)

        node_to_detach = reference_link.child
        detach_from = reference_link.parent
        validator = DetachAuthorizedRelationshipValidator(self.tree, node_to_detach, detach_from)

        self.assertFalse(validator.is_valid())
        expected_error_msg = _("The parent must have at least one child of type(s) \"%(types)s\".") % {
            "types": str(child_type_under_reference.value)
        }
        self.assertListEqual(
            [expected_error_msg],
            validator.error_messages,
            "Should validate types of the children of the child linked by reference"
        )


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

from base.models.authorized_relationship import AuthorizedRelationshipList
from base.models.enums.education_group_types import TrainingType, GroupType
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipObjectFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory


class TestInit(SimpleTestCase):
    def test_normal_usage(self):
        auth_relations = [AuthorizedRelationshipObjectFactory()]
        result = AuthorizedRelationshipList(auth_relations)
        self.assertEqual(auth_relations, result.authorized_relationships)

    def test_when_authorized_relationships_arg_is_none(self):
        with self.assertRaises(AssertionError):
            AuthorizedRelationshipList(None)

    def test_when_authorized_relationships_arg_is_not_a_list(self):
        with self.assertRaises(AssertionError):
            AuthorizedRelationshipList("I'm not a list")

    def test_when_authorized_relationships_arg_is_empty(self):
        with self.assertRaises(AssertionError):
            AuthorizedRelationshipList([])

    def test_when_authorized_relationships_arg_is_wrong_instance(self):
        with self.assertRaises(AssertionError):
            wrong_instance = NodeGroupYearFactory()
            AuthorizedRelationshipList([wrong_instance])


class TestGetAuthorizedRelationship(SimpleTestCase):

    def setUp(self):
        self.auth_relation = AuthorizedRelationshipObjectFactory(
            parent_type=TrainingType.BACHELOR, child_type=GroupType.COMMON_CORE
        )
        self.auth_relations = AuthorizedRelationshipList([self.auth_relation])
        self.authorized_parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        self.authorized_child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)

    def test_when_child_type_matches_but_not_parent_type(self):
        unauthorized_child = NodeGroupYearFactory(node_type=TrainingType.ACCESS_CONTEST)
        result = self.auth_relations.get_authorized_relationship(
            self.authorized_parent.node_type,
            unauthorized_child.node_type
        )
        self.assertIsNone(result)

    def test_when_parent_type_matches_but_not_parent_type(self):
        unauthorized_parent = NodeGroupYearFactory(node_type=TrainingType.INTERNSHIP)
        result = self.auth_relations.get_authorized_relationship(
            unauthorized_parent.node_type,
            self.authorized_child.node_type
        )
        self.assertIsNone(result)

    def test_when_parent_type_and_child_type_matches(self):
        parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        result = self.auth_relations.get_authorized_relationship(parent.node_type, child.node_type)
        self.assertEqual(self.auth_relation, result)


class TestIsAuthorized(SimpleTestCase):

    def setUp(self):
        self.auth_relation = AuthorizedRelationshipObjectFactory(
            parent_type=TrainingType.BACHELOR, child_type=GroupType.COMMON_CORE
        )
        self.auth_relations = AuthorizedRelationshipList([self.auth_relation])

    def test_when_is_authorized(self):
        parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        result = self.auth_relations.get_authorized_relationship(parent.node_type, child.node_type)
        self.assertTrue(result)

    def test_when_is_not_authorized(self):
        parent = NodeGroupYearFactory(node_type=TrainingType.INTERNSHIP)
        child = NodeGroupYearFactory(node_type=GroupType.FINALITY_120_LIST_CHOICE)
        result = self.auth_relations.get_authorized_relationship(parent.node_type, child.node_type)
        self.assertFalse(result)


class TestGetAuthorizedChildrenTypes(SimpleTestCase):

    def setUp(self):
        self.auth_relation = AuthorizedRelationshipObjectFactory(
            parent_type=TrainingType.BACHELOR, child_type=GroupType.COMMON_CORE
        )
        self.auth_relations = AuthorizedRelationshipList([self.auth_relation])
        self.authorized_parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        self.authorized_child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)

    def test_result_is_a_set_instance(self):
        error_msg = """Using a set() for performance"""
        result = self.auth_relations.get_authorized_children_types(self.authorized_parent.node_type)
        self.assertIsInstance(result, set, error_msg)

    def test_when_child_type_unauthorized(self):
        parent_without_authorized_children = NodeGroupYearFactory(node_type=TrainingType.ACCESS_CONTEST)
        result = self.auth_relations.get_authorized_children_types(parent_without_authorized_children.node_type)
        self.assertEqual(set(), result)

    def test_when_child_type_unauthorized_is_learning_unit(self):
        parent_without_authorized_children = NodeGroupYearFactory(node_type=NodeType.LEARNING_UNIT)
        result = self.auth_relations.get_authorized_children_types(parent_without_authorized_children.node_type)
        self.assertEqual(set(), result)

    def test_when_child_type_authorized(self):
        result = self.auth_relations.get_authorized_children_types(self.authorized_parent.node_type)
        expected_result = {
            self.authorized_child.node_type
        }
        self.assertSetEqual(expected_result, result)

    def test_when_child_type_authorized_is_learning_unit(self):
        another_authorized_relation = AuthorizedRelationshipObjectFactory(
            parent_type=TrainingType.BACHELOR, child_type=NodeType.LEARNING_UNIT
        )
        authorized_relations = AuthorizedRelationshipList([another_authorized_relation])

        result = authorized_relations.get_authorized_children_types(TrainingType.BACHELOR)
        expected_result = {
            NodeType.LEARNING_UNIT
        }
        self.assertSetEqual(expected_result, result)

    def test_when_multiple_children_authorized(self):
        another_authorized_relation = AuthorizedRelationshipObjectFactory(
            parent_type=TrainingType.BACHELOR, child_type=GroupType.SUB_GROUP
        )
        authorized_relations = AuthorizedRelationshipList([self.auth_relation, another_authorized_relation])
        another_authorized_child = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP)
        result = authorized_relations.get_authorized_children_types(self.authorized_parent.node_type)
        expected_result = {
            self.authorized_child.node_type,
            another_authorized_child.node_type
        }
        self.assertSetEqual(expected_result, result)


class TestGetOrderedMandatoryChildrenTypes(SimpleTestCase):

    def setUp(self):
        self.parent_type = TrainingType.PGRM_MASTER_120
        self.common_core_relation = AuthorizedRelationshipObjectFactory(
            parent_type=self.parent_type, child_type=GroupType.COMMON_CORE, min_constraint=1
        )
        self.option_list_relation = AuthorizedRelationshipObjectFactory(
            parent_type=self.parent_type, child_type=GroupType.OPTION_LIST_CHOICE, min_constraint=1
        )
        self.finality_list_relation = AuthorizedRelationshipObjectFactory(
            parent_type=self.parent_type, child_type=GroupType.FINALITY_120_LIST_CHOICE, min_constraint=1
        )

    def test_ordering(self):

        wrong_order = [self.option_list_relation, self.finality_list_relation, self.common_core_relation]
        authorized_relations = AuthorizedRelationshipList(wrong_order)

        result = authorized_relations.get_ordered_mandatory_children_types(self.parent_type)
        expected_order = [
            self.common_core_relation.child_type,
            self.finality_list_relation.child_type,
            self.option_list_relation.child_type
        ]
        self.assertListEqual(result, expected_order)

    def test_when_relation_min_authorized_is_0(self):
        other_relation = AuthorizedRelationshipObjectFactory(
            parent_type=self.parent_type, child_type=GroupType.SUB_GROUP, min_constraint=0
        )
        authorized_relations = AuthorizedRelationshipList([other_relation])
        self.assertListEqual([], authorized_relations.get_ordered_mandatory_children_types(self.parent_type))

    def test_when_relation_is_with_learning_unit(self):
        other_relation = AuthorizedRelationshipObjectFactory(
            parent_type=self.parent_type, child_type=NodeType.LEARNING_UNIT, min_constraint=1
        )
        authorized_relations = AuthorizedRelationshipList([other_relation])
        self.assertListEqual([], authorized_relations.get_ordered_mandatory_children_types(self.parent_type))

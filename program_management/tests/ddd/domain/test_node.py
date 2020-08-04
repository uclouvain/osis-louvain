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

from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from base.models.enums.link_type import LinkTypes
from education_group.enums.node_type import NodeType
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory


class TestAddChildNode(SimpleTestCase):
    def test_add_child_to_node(self):
        group_year_node = NodeGroupYearFactory(node_id=0, code="LDROI200G", title="Tronc commun", year=2018)
        learning_unit_year_node = NodeLearningUnitYearFactory(
            node_id=2,
            code="LDROI100",
            title="Introduction",
            year=2018
        )

        link_created = group_year_node.add_child(learning_unit_year_node, relative_credits=5, comment='Dummy comment')
        self.assertIn(link_created, group_year_node.children)

        self.assertEqual(link_created.relative_credits, 5)
        self.assertEqual(link_created.comment, 'Dummy comment')

    def test_assert_order_correctly_computed(self):
        group_year_node = NodeGroupYearFactory(node_id=0, code="LDROI100T", title="Tronc commun", year=2018)
        subgroup_node = NodeGroupYearFactory(node_id=1, code="LDROI100R", title="Sous-groupe", year=2018)
        learning_unit_year_node = NodeLearningUnitYearFactory(
            node_id=2,
            code="LDROI100",
            title="Introduction",
            year=2018
        )

        link_1_created = group_year_node.add_child(subgroup_node)
        link_2_created = group_year_node.add_child(learning_unit_year_node)

        self.assertEqual(link_1_created.order, 0)
        self.assertEqual(link_2_created.order, 1)


class TestDescendentsPropertyNode(SimpleTestCase):
    def setUp(self):
        self.root_node = NodeGroupYearFactory(node_id=0, code="LDROI200T", title="Tronc commun", year=2018)
        self.subgroup_node = NodeGroupYearFactory(node_id=1, code="LDROI200G", title="Sub group", year=2018)
        self.leaf = NodeLearningUnitYearFactory(node_id=2, code="LDROI100", title="Introduction", year=2018)

    def test_case_no_descendents(self):
        self.assertIsInstance(self.root_node.descendents, dict)
        self.assertEqual(self.root_node.descendents, {})

    def test_case_all_descendents_with_path_as_key(self):
        self.subgroup_node.add_child(self.leaf)
        self.root_node.add_child(self.subgroup_node)

        self.assertIsInstance(self.root_node.descendents, dict)
        expected_keys = [
            "|".join([str(self.root_node.pk), str(self.subgroup_node.pk)]),   # First level
            "|".join([str(self.root_node.pk), str(self.subgroup_node.pk), str(self.leaf.pk)]),  # Second level
        ]
        self.assertTrue(all(k in expected_keys for k in self.root_node.descendents.keys()))


class TestEq(SimpleTestCase):

    def test_should_return_true_when_the_entity_id_are_equals(self):
        node = NodeGroupYearFactory()
        node_with_same_identity = NodeGroupYearFactory(code=node.code, year=node.year)
        self.assertTrue(node == node_with_same_identity)

    def test_when_should_return_false_when_entity_id_are_not_equals(self):
        node = NodeGroupYearFactory()
        node_with_different_identity = NodeGroupYearFactory(year=node.year+1)
        self.assertFalse(node == node_with_different_identity)


class TestStr(SimpleTestCase):

    def setUp(self):
        code = 'Code'
        year = 2019
        self.node_group_year = NodeGroupYearFactory(code=code, year=year)
        self.node_learning_unit = NodeLearningUnitYearFactory(code=code, year=year)

    def test_node_group_year_str(self):
        self.assertEqual(str(self.node_group_year), 'Code (2019)')

    def test_node_learning_unit_str(self):
        self.assertEqual(str(self.node_learning_unit), 'Code (2019)')


class TestGetChildrenTypes(SimpleTestCase):

    def test_when_no_children(self):
        node = NodeGroupYearFactory()
        self.assertEqual([], node.get_children_types())

    def test_when_link_type_is_none__incudes_reference_kwarg_true(self):
        link = LinkFactory(link_type=None)
        child_node_type = link.child.node_type
        result = link.parent.get_children_types(include_nodes_used_as_reference=True)
        self.assertListEqual(
            [child_node_type],
            result
        )

    def test_when_link_type_is_reference__incudes_reference_kwarg_true(self):
        error_msg = """
            A 'REFERENCE' link means that we should ignore the child node, 
            and consider the children of the child as there were direct children
        """
        link0 = LinkFactory(
            parent__node_type=TrainingType.BACHELOR,
            child__node_type=GroupType.SUB_GROUP,
            link_type=LinkTypes.REFERENCE
        )
        link1 = LinkFactory(
            parent=link0.child,
            child__node_type=GroupType.COMMON_CORE,
            link_type=None
        )
        result = link0.parent.get_children_types(include_nodes_used_as_reference=True)
        self.assertListEqual(
            [link1.child.node_type],
            result,
            error_msg
        )
        self.assertNotIn(link0.child.node_type, result, error_msg)

    def test_when_2_levels_link_type_reference(self):
        error_msg = """
            A 'REFERENCE' link means that we should ignore the child node, 
            and consider the children of the child as there were direct children
        """
        link0 = LinkFactory(link_type=LinkTypes.REFERENCE)
        link1 = LinkFactory(parent=link0.child, link_type=LinkTypes.REFERENCE)
        link2 = LinkFactory(parent=link1.child, child__minitraining=True, link_type=None)
        result = link0.parent.get_children_types(include_nodes_used_as_reference=True)
        self.assertListEqual(
            [link2.child.node_type],
            result,
            error_msg
        )
        self.assertNotIn(link0.child.node_type, result, error_msg)


class TestGetChildrenAndReferenceChildren(SimpleTestCase):
    def test_when_no_children(self):
        node = NodeGroupYearFactory()
        self.assertEqual([], node.children_and_reference_children())

    def test_get_only_children_of_reference_link(self):
        link = LinkFactory(link_type=LinkTypes.REFERENCE)
        LinkFactory(parent=link.child)
        result = link.parent.children_and_reference_children()
        self.assertListEqual(
            link.child.children,
            result
        )

    def test_get_only_children_of_reference_link_except_within_minor_list(self):
        minor_list = NodeGroupYearFactory(node_type=GroupType.MINOR_LIST_CHOICE)
        link_ref = LinkFactory(link_type=LinkTypes.REFERENCE, parent=minor_list)
        LinkFactory(parent=link_ref.child)
        result = link_ref.parent.get_children_and_only_reference_children_except_within_minor_list()
        self.assertListEqual(
            [link_ref],
            result
        )


class TestGetAllChildrenAsNode(SimpleTestCase):

    def test_when_no_child(self):
        node = NodeGroupYearFactory()
        self.assertEqual(set(), node.get_all_children_as_nodes())

    def test_when_2_children_level(self):
        link1 = LinkFactory()
        link2 = LinkFactory(parent=link1.child)
        result = link1.parent.get_all_children_as_nodes()
        expected_result = {link2.parent, link2.child}
        self.assertEqual(expected_result, result)

    def test_when_kwarg_ignore_children_from_is_set(self):
        link1 = LinkFactory(parent__node_type=TrainingType.BACHELOR, child__node_type=GroupType.MINOR_LIST_CHOICE)
        link1_1 = LinkFactory(parent=link1.parent, child__node_type=GroupType.COMMON_CORE)
        link1_2_1 = LinkFactory(parent=link1.child, child__node_type=MiniTrainingType.ACCESS_MINOR)
        result = link1.parent.get_all_children_as_nodes(
            ignore_children_from={GroupType.MINOR_LIST_CHOICE}
        )
        self.assertNotIn(link1_2_1.child, result)

        expected_result = {
            link1.child,
            link1_1.child,
        }
        self.assertSetEqual(result, expected_result)

    def test_when_kwarg_take_only_is_set(self):
        link1 = LinkFactory(
            parent__node_type=TrainingType.PGRM_MASTER_120,
            child__node_type=GroupType.OPTION_LIST_CHOICE
        )
        link1_1 = LinkFactory(parent=link1.parent, child__node_type=TrainingType.MASTER_MA_120)
        link1_1_1 = LinkFactory(parent=link1_1.child, child__node_type=MiniTrainingType.OPTION)
        link1_2_1 = LinkFactory(parent=link1.child, child__node_type=MiniTrainingType.OPTION)
        result = link1.parent.get_all_children_as_nodes(
            take_only={MiniTrainingType.OPTION}
        )

        expected_result = {
            link1_1_1.child,
            link1_2_1.child,
        }
        self.assertSetEqual(result, expected_result)


class TestGetIsPrerequisiteOf(SimpleTestCase):

    def test_when_is_prerequisite_of_nothing(self):
        node = NodeLearningUnitYearFactory(is_prerequisite_of=[])
        self.assertEqual(node.get_is_prerequisite_of(), [])

    def test_when_id_prerequisite_of_mutliple_nodes(self):
        multiple_nodes = [NodeLearningUnitYearFactory(), NodeLearningUnitYearFactory()]
        node = NodeLearningUnitYearFactory(is_prerequisite_of=multiple_nodes)
        self.assertListEqual(node.get_is_prerequisite_of(), multiple_nodes)

    def test_ordering(self):
        ldroi1002 = NodeLearningUnitYearFactory(code='LDROI1002')
        lecge1010 = NodeLearningUnitYearFactory(code='LECGE1010')
        ldroi1001 = NodeLearningUnitYearFactory(code='LDROI1001')

        wrong_order = [lecge1010, ldroi1002, ldroi1001]
        node = NodeLearningUnitYearFactory(is_prerequisite_of=wrong_order)

        error_msg = "This order is used to order prerequisite nodes in excel file."
        expected_result = [ldroi1001, ldroi1002, lecge1010]
        self.assertListEqual(node.get_is_prerequisite_of(), expected_result, error_msg)


class TestGetAllChildrenAsLearningUnitNodes(SimpleTestCase):

    def setUp(self):
        self.parent = NodeGroupYearFactory()

    def test_when_contains_children_of_type_group(self):
        LinkFactory(parent=self.parent, child__node_type=NodeType.GROUP)
        result = self.parent.get_all_children_as_learning_unit_nodes()
        self.assertEqual(result, [])

    def test_when_has_no_children(self):
        result = self.parent.get_all_children_as_learning_unit_nodes()
        self.assertEqual(result, [])

    def test_ordering(self):
        link0 = LinkFactory(parent=self.parent, child=NodeLearningUnitYearFactory(), order=0)
        link2 = LinkFactory(parent=self.parent, child=NodeLearningUnitYearFactory(), order=2)
        link1 = LinkFactory(parent=self.parent, child=NodeLearningUnitYearFactory(), order=1)
        result = self.parent.get_all_children_as_learning_unit_nodes()
        exepcted_order = [link0.child, link1.child, link2.child]
        error_msg = "This order is used for prerequisites in excel file."
        self.assertListEqual(result, exepcted_order, error_msg)


class TestChildren(SimpleTestCase):

    def setUp(self):
        self.parent = NodeGroupYearFactory()

    def test_return_empty_list_when_no_children(self):
        self.assertEqual(
            self.parent.children,
            []
        )

    def test_returns_children_ordered_by_order(self):
        link0 = LinkFactory(parent=self.parent, child=NodeLearningUnitYearFactory(), order=0)
        link2 = LinkFactory(parent=self.parent, child=NodeLearningUnitYearFactory(), order=2)
        link1 = LinkFactory(parent=self.parent, child=NodeLearningUnitYearFactory(), order=1)
        self.assertEqual(
            self.parent.children,
            [link0, link1, link2]
        )


class TestDetachChild(SimpleTestCase):
    def test_when_child_not_in_children(self):
        link = LinkFactory()
        unexisting_child = NodeGroupYearFactory()
        with self.assertRaises(StopIteration):
            link.parent.detach_child(unexisting_child)

    def test_when_child_is_correctly_detached(self):
        common_parent = NodeGroupYearFactory()
        link1 = LinkFactory(parent=common_parent)
        link2 = LinkFactory(parent=common_parent)
        link3 = LinkFactory(parent=common_parent)

        link_deleted = common_parent.detach_child(link1.child)

        assertion_msg = "Link {} should have been removed from children".format(link1)
        self.assertNotIn(link_deleted, common_parent.children, assertion_msg)

        assertion_msg = "Link {} should have been added to deleted children".format(link1)
        self.assertIn(link_deleted, common_parent._deleted_children, assertion_msg)


class TestIsOption(SimpleTestCase):
    def test_when_node_is_option(self):
        node = NodeGroupYearFactory(node_type=MiniTrainingType.OPTION)
        self.assertTrue(node.is_option())

    def test_when_node_is_not_option(self):
        node = NodeGroupYearFactory(node_type=MiniTrainingType.ACCESS_MINOR)
        self.assertFalse(node.is_option())


class TestGetOptionsList(SimpleTestCase):
    def test_when_has_no_children(self):
        node = NodeGroupYearFactory()
        self.assertEqual(node.get_option_list(), set())

    def test_when_node_is_option(self):
        node = NodeGroupYearFactory(node_type=MiniTrainingType.OPTION)
        self.assertEqual(node.get_option_list(), set(), "Should not contains himself in children options list")

    def test_when_has_direct_child_option(self):
        link = LinkFactory(child__node_type=MiniTrainingType.OPTION)
        expected_result = {link.child}
        self.assertEqual(link.parent.get_option_list(), expected_result, "Should contain direct children")

    def test_when_sub_child_is_option(self):
        link1 = LinkFactory(child__node_type=GroupType.OPTION_LIST_CHOICE)
        link2 = LinkFactory(parent=link1.child, child__node_type=MiniTrainingType.OPTION)
        expected_result = {link2.child}
        self.assertEqual(link2.parent.get_option_list(), expected_result, "Should contain children of children")


class TestUpDownChild(SimpleTestCase):
    def setUp(self) -> None:
        self.parent_node = NodeGroupYearFactory()
        self.link1 = LinkFactory(parent=self.parent_node, order=0)
        self.link2 = LinkFactory(parent=self.parent_node, order=1)
        self.link3 = LinkFactory(parent=self.parent_node, order=2)

    def test_should_not_change_order_when_applying_up_on_first_link(self):
        self.parent_node.up_child(self.link1.child)

        self.assertListEqual(
            self.parent_node.children,
            [self.link1, self.link2, self.link3]
        )

    def test_should_not_change_order_when_applying_down_on_last_link(self):
        self.parent_node.down_child(self.link3.child)

        self.assertListEqual(
            self.parent_node.children,
            [self.link1, self.link2, self.link3]
        )

    def test_should_not_change_order_when_applying_up_then_down_on_link(self):
        self.parent_node.up_child(self.link2.child)

        self.assertListEqual(
            self.parent_node.children,
            [self.link2, self.link1, self.link3]
        )

        self.parent_node.down_child(self.link2.child)
        self.assertListEqual(
            self.parent_node.children,
            [self.link1, self.link2, self.link3]
        )


class TestGetFinalitiesList(SimpleTestCase):
    def test_when_has_no_children(self):
        node = NodeGroupYearFactory()
        self.assertEqual(node.get_finality_list(), set())

    def test_when_node_is_finality(self):
        node = NodeGroupYearFactory(node_type=TrainingType.MASTER_MS_120)
        self.assertEqual(node.get_finality_list(), set(), "Should not contains himself in children finalities list")

    def test_when_has_direct_child_finality(self):
        link = LinkFactory(child__node_type=TrainingType.MASTER_MS_120)
        expected_result = {link.child}
        self.assertEqual(link.parent.get_finality_list(), expected_result, "Should contain direct children")

    def test_when_sub_child_is_finality(self):
        link1 = LinkFactory(child__node_type=GroupType.FINALITY_120_LIST_CHOICE)
        link2 = LinkFactory(parent=link1.child, child__node_type=TrainingType.MASTER_MS_120)
        expected_result = {link2.child}
        self.assertEqual(link2.parent.get_finality_list(), expected_result, "Should contain children of children")


class TestGetDirectChildrenAsNodes(SimpleTestCase):
    def setUp(self):
        self.parent = NodeGroupYearFactory()
        self.child_link_0 = LinkFactory(
            parent=self.parent,
            child=NodeGroupYearFactory(node_type=GroupType.COMMON_CORE),
            order=0
        )
        self.child_link_1 = LinkFactory(
            parent=self.parent,
            child=NodeGroupYearFactory(node_type=GroupType.MAJOR_LIST_CHOICE),
            order=1
        )

    def test_assert_return_empty_list_when_no_children(self):
        self.assertEqual(
            NodeGroupYearFactory().get_direct_children_as_nodes(),
            []
        )

    def test_assert_filter_take_only(self):
        self.assertEqual(
            self.parent.get_direct_children_as_nodes(take_only={GroupType.COMMON_CORE}),
            [self.child_link_0.child]
        )

    def test_assert_filter_ignore_children_from(self):
        self.assertEqual(
            self.parent.get_direct_children_as_nodes(ignore_children_from={GroupType.COMMON_CORE}),
            [self.child_link_1.child]
        )


class TestUpdateLinkOfDirectChildNode(SimpleTestCase):
    def test_assert_has_changed_property(self):
        parent = NodeGroupYearFactory()
        child_link_0 = LinkFactory(
            parent=parent,
            child=NodeGroupYearFactory(node_type=GroupType.COMMON_CORE),
            order=0
        )

        link_updated = parent.update_link_of_direct_child_node(
            child_id=child_link_0.child.entity_id,
            relative_credits=0,
            access_condition=False,
            is_mandatory=False,
            block=1,
            link_type=None,
            comment="",
            comment_english="english"
        )
        self.assertTrue(link_updated._has_changed)

    def test_assert_link_type_reference_when_parent_major_minor_list_choice_and_child_other(self):
        minor_list_choice = NodeGroupYearFactory(node_type=GroupType.MINOR_LIST_CHOICE)
        child_link = LinkFactory(
            parent=minor_list_choice,
            child=NodeGroupYearFactory(node_type=GroupType.SUB_GROUP),
            order=0
        )

        link_updated = minor_list_choice.update_link_of_direct_child_node(
            child_id=child_link.child.entity_id,
            relative_credits=0,
            access_condition=True,
            is_mandatory=True,
            block=1,
            link_type=None,
            comment="",
            comment_english="english"
        )
        self.assertEqual(link_updated.link_type, LinkTypes.REFERENCE)

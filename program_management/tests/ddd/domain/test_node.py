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

        group_year_node.add_child(learning_unit_year_node, relative_credits=5, comment='Dummy comment')
        self.assertEquals(len(group_year_node.children), 1)

        self.assertEquals(group_year_node.children[0].relative_credits, 5)
        self.assertEquals(group_year_node.children[0].comment, 'Dummy comment')


class TestDescendentsPropertyNode(SimpleTestCase):
    def setUp(self):
        self.root_node = NodeGroupYearFactory(node_id=0, code="LDROI200T", title="Tronc commun", year=2018)
        self.subgroup_node = NodeGroupYearFactory(node_id=1, code="LDROI200G", title="Sub group", year=2018)
        self.leaf = NodeLearningUnitYearFactory(node_id=2, code="LDROI100", title="Introduction", year=2018)

    def test_case_no_descendents(self):
        self.assertIsInstance(self.root_node.descendents, dict)
        self.assertEquals(self.root_node.descendents, {})

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

    def setUp(self):
        self.node_id = 1
        self.node = NodeGroupYearFactory(node_id=1)

    def test_when_nodes_group_year_are_equal(self):
        node_with_same_id = NodeGroupYearFactory(node_id=self.node_id)
        self.assertTrue(self.node == node_with_same_id)

    def test_when_nodes_group_year_are_not_equal(self):
        node_with_different_id = NodeGroupYearFactory(node_id=self.node_id + 1)
        self.assertFalse(self.node == node_with_different_id)

    def test_when_nodes_learning_unit_are_equal(self):
        node_with_same_id = NodeLearningUnitYearFactory(node_id=self.node_id)
        self.assertFalse(self.node == node_with_same_id)

    def test_when_nodes_learning_unit_are_not_equal(self):
        node_with_different_id = NodeLearningUnitYearFactory(node_id=self.node_id + 1)
        self.assertFalse(self.node == node_with_different_id)


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
        node = NodeLearningUnitYearFactory(is_prerequisite_of=None)
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

        common_parent.detach_child(link1.child)

        expected_result = [link2, link3]
        assertion_msg = "Link {} should have been removed from children".format(link1)
        self.assertListEqual(common_parent.children, expected_result, assertion_msg)

        assertion_msg = "Link {} should have been added to deleted children".format(link1)
        expected_result = {link1}
        self.assertSetEqual(common_parent._deleted_children, expected_result,assertion_msg)


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

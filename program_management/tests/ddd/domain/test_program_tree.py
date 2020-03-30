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
import inspect

from django.test import SimpleTestCase

from base.ddd.utils.validation_message import MessageLevel
from base.models.enums.education_group_types import TrainingType, GroupType
from base.models.enums.link_type import LinkTypes
from program_management.ddd.domain import node
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.validators.validators_by_business_action import AttachNodeValidatorList
from program_management.models.enums import node_type
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeEducationGroupYearFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.service.mixins import ValidatorPatcherMixin


class TestGetNodeProgramTree(SimpleTestCase):
    def setUp(self):
        link = LinkFactory()
        self.root_node = link.parent
        self.subgroup_node = link.child
        self.tree = ProgramTreeFactory(root_node=self.root_node)

    def test_get_node_case_invalid_path(self):
        with self.assertRaises(node.NodeNotFoundException):
            self.tree.get_node(path='dummy_path')

    def test_get_node_case_children_path(self):
        valid_path = "|".join([str(self.root_node.pk), str(self.subgroup_node.pk)])
        result_node = self.tree.get_node(path=valid_path)

        self.assertEquals(result_node.pk, self.subgroup_node.pk)

    def test_get_node_case_root_node_path(self):
        result_node = self.tree.get_node(path=str(self.root_node.pk))
        self.assertEquals(
            result_node.pk,
            self.root_node.pk
        )


class TestGetNodeByIdAndClassProgramTree(SimpleTestCase):
    def setUp(self):
        link = LinkFactory(child=NodeGroupYearFactory(node_id=1))
        self.root_node = link.parent
        self.subgroup_node = link.child

        link_with_learning_unit = LinkFactory(parent=self.root_node, child=NodeLearningUnitYearFactory(node_id=1))
        self.learning_unit_node = link_with_learning_unit.child

        self.tree = ProgramTreeFactory(root_node=self.root_node)

    def test_should_return_None_when_no_node_present_with_corresponding_node_id(self):
        result = self.tree.get_node_by_id_and_class(2, node.NodeLearningUnitYear)
        self.assertIsNone(result)

    def test_should_return_node_matching_specific_node_id_with_respect_to_class(self):
        result = self.tree.get_node_by_id_and_class(1, node.NodeLearningUnitYear)
        self.assertEqual(
            result,
            self.learning_unit_node
        )

        result = self.tree.get_node_by_id_and_class(1, node.NodeGroupYear)
        self.assertEqual(
            result,
            self.subgroup_node
        )


class TestGetCNodesByType(SimpleTestCase):
    def setUp(self):
        link = LinkFactory(child=NodeGroupYearFactory())
        self.root_node = link.parent
        self.subgroup_node = link.child

        self.tree = ProgramTreeFactory(root_node=self.root_node)

    def test_should_return_empty_list_if_no_matching_type(self):
        result = self.tree.get_nodes_by_type(node_type.NodeType.EDUCATION_GROUP)
        self.assertCountEqual(
            result,
            []
        )

    def test_should_return_all_nodes_with_specific_node_type(self):
        result = self.tree.get_nodes_by_type(node_type.NodeType.GROUP)
        self.assertCountEqual(
            result,
            [self.subgroup_node, self.root_node]
        )


class TestGetCodesPermittedAsPrerequisite(SimpleTestCase):
    def setUp(self):
        link = LinkFactory(child=NodeGroupYearFactory())
        self.root_node = link.parent
        self.subgroup_node = link.child

        self.tree = ProgramTreeFactory(root_node=self.root_node)

    def test_should_return_codes_of_all_learning_unit_nodes(self):
        LinkFactory(parent=self.root_node, child=NodeLearningUnitYearFactory(code='LOSIS452'))
        LinkFactory(parent=self.root_node, child=NodeLearningUnitYearFactory(code="LT"))

        result = self.tree.get_codes_permitted_as_prerequisite()
        self.assertCountEqual(
            result,
            ["LOSIS452", "LT"]
        )


class TestAttachNodeProgramTree(SimpleTestCase, ValidatorPatcherMixin):
    def setUp(self):
        root_node = NodeGroupYearFactory(node_id=0)
        self.tree = ProgramTreeFactory(root_node=root_node)

    def test_attach_node_case_no_path_specified(self):
        self.mock_validator(AttachNodeValidatorList, ['Success msg'], level=MessageLevel.SUCCESS)
        subgroup_node = NodeGroupYearFactory()
        self.tree.attach_node(subgroup_node)
        self.assertIn(subgroup_node, self.tree.root_node.children_as_nodes)

    def test_attach_node_case_path_specified_found(self):
        self.mock_validator(AttachNodeValidatorList, ['Success msg'], level=MessageLevel.SUCCESS)
        subgroup_node = NodeGroupYearFactory()
        self.tree.attach_node(subgroup_node)

        node_to_attach = NodeGroupYearFactory()
        path = "|".join([str(self.tree.root_node.pk), str(subgroup_node.pk)])
        self.tree.attach_node(node_to_attach, path=path)

        self.assertIn(node_to_attach, self.tree.get_node(path).children_as_nodes)

    def test_when_validator_list_is_valid(self):
        self.mock_validator(AttachNodeValidatorList, ['Success message text'], level=MessageLevel.SUCCESS)
        path = str(self.tree.root_node.node_id)
        child_to_attach = NodeGroupYearFactory()
        result = self.tree.attach_node(child_to_attach, path=path)
        self.assertEqual(result[0], 'Success message text')
        self.assertEqual(1, len(result))
        self.assertIn(child_to_attach, self.tree.root_node.children_as_nodes)

    def test_when_validator_list_is_not_valid(self):
        self.mock_validator(AttachNodeValidatorList, ['error message text'], level=MessageLevel.ERROR)
        path = str(self.tree.root_node.node_id)
        child_to_attach = NodeGroupYearFactory()
        result = self.tree.attach_node(child_to_attach, path=path)
        self.assertEqual(result[0], 'error message text')
        self.assertEqual(1, len(result))
        self.assertNotIn(child_to_attach, self.tree.root_node.children_as_nodes)


class TestDetachNodeProgramTree(SimpleTestCase):
    def setUp(self):
        self.link1 = LinkFactory()
        self.link2 = LinkFactory(parent=self.link1.child)
        self.tree = ProgramTreeFactory(root_node=self.link1.parent)

    def test_detach_node_case_invalid_path(self):
        with self.assertRaises(node.NodeNotFoundException):
            self.tree.detach_node(path="dummy_path")

    def test_detach_node_case_valid_path(self):
        path_to_detach = "|".join([
            str(self.link1.parent.pk),
            str(self.link1.child.pk),
            str(self.link2.child.pk),
        ])

        self.tree.detach_node(path_to_detach)
        self.assertListEqual(
            self.tree.root_node.children[0].child.children,  # root_node/common_core
            []
        )

    def test_detach_node_case_try_to_detach_root_node(self):
        with self.assertRaises(Exception):
            self.tree.detach_node(str(self.link1.parent.pk))


class TestGetParentsUsingNodeAsReference(SimpleTestCase):
    def setUp(self):
        self.link_with_root = LinkFactory(parent__title='ROOT', child__title='child_ROOT')
        self.tree = ProgramTreeFactory(root_node=self.link_with_root.parent)

        self.link_with_ref = LinkFactory(
            parent=self.link_with_root.child,
            child__title='child__child__ROOT',
            link_type=LinkTypes.REFERENCE,
        )

    def test_when_node_is_not_used_as_reference(self):
        link_without_ref = LinkFactory(parent=self.link_with_root.child, link_type=None)
        result = self.tree.get_parents_using_node_as_reference(link_without_ref.child)
        self.assertListEqual(result, [])

    def test_when_node_is_used_as_reference(self):
        result = self.tree.get_parents_using_node_as_reference(self.link_with_ref.child)
        self.assertListEqual(
            result,
            [self.link_with_ref.parent]
        )

    def test_when_node_is_used_as_reference_twice(self):
        child_used_twice = self.link_with_ref.child

        another_link = LinkFactory(parent=self.link_with_root.parent)
        another_link_with_ref = LinkFactory(
            parent=another_link.child,
            child=child_used_twice,
            link_type=LinkTypes.REFERENCE
        )

        result = self.tree.get_parents_using_node_as_reference(child_used_twice)

        self.assertCountEqual(result, [self.link_with_ref.parent, another_link_with_ref.parent])


class TestGetParents(SimpleTestCase):
    def setUp(self):
        self.link_with_root = LinkFactory(parent__title='ROOT', child__title='child_ROOT')
        self.tree = ProgramTreeFactory(root_node=self.link_with_root.parent)

        self.link_with_child = LinkFactory(
            parent=self.link_with_root.child,
            child__title='child__child__ROOT',
        )

        self.path = '{level1}|{level2}|{level3}'.format(
            level1=self.link_with_root.parent.node_id,
            level2=self.link_with_root.child.node_id,
            level3=self.link_with_child.child.node_id
        )

    def test_when_child_has_parents_on_2_levels(self):
        result = self.tree.get_parents(self.path)
        self.assertListEqual(
            result,
            [self.link_with_root.child, self.link_with_root.parent]
        )

    def test_when_child_has_multiple_parents(self):
        another_link_with_root = LinkFactory(parent=self.link_with_root.parent)
        another_link_with_child = LinkFactory(parent=another_link_with_root.child, child=self.link_with_child.child)
        result = self.tree.get_parents(self.path)

        self.assertNotIn(another_link_with_root.child, result)

        self.assertListEqual(
            result,
            [self.link_with_root.child, self.link_with_root.parent]
        )

    def test_when_infinite_loop(self):
        LinkFactory(parent=self.link_with_child.child, child=self.link_with_root.parent)
        with self.assertRaises(RecursionError):
            self.tree.get_parents(self.path)


class TestGetAllNodes(SimpleTestCase):

    def test_when_tree_has_not_children(self):
        tree = ProgramTreeFactory()
        self.assertSetEqual(tree.get_all_nodes(), {tree.root_node}, 'All nodes must include the root node')

    def test_when_tree_has_nodes_in_multiple_levels(self):
        link_with_root = LinkFactory(parent__title='ROOT', child__title='child_ROOT')
        link_with_child = LinkFactory(
            parent=link_with_root.child,
            child__title='child__child__ROOT',
        )
        tree = ProgramTreeFactory(root_node=link_with_root.parent)
        result = tree.get_all_nodes()
        self.assertSetEqual(
            result,
            {link_with_root.parent, link_with_root.child, link_with_child.child}
        )


class TestGetFirstLinkOccurenceUsingNode(SimpleTestCase):

    def setUp(self):
        self.tree = ProgramTreeFactory()
        self.child_reused = NodeGroupYearFactory()

    def test_when_child_not_used(self):
        LinkFactory(parent=self.tree.root_node)
        result = self.tree.get_first_link_occurence_using_node(self.child_reused)
        self.assertEqual(result, None)

    def test_when_child_used_only_one_time_in_tree(self):
        link1 = LinkFactory(parent=self.tree.root_node)
        link1_1 = LinkFactory(parent=link1.child, child=self.child_reused)
        result = self.tree.get_first_link_occurence_using_node(self.child_reused)
        self.assertEqual(result, link1_1)

    def test_with_child_reused_in_tree(self):
        link1 = LinkFactory(parent=self.tree.root_node)
        link1_1 = LinkFactory(parent=link1.child, child=self.child_reused)
        link2 = LinkFactory(parent=self.tree.root_node)
        link2_1 = LinkFactory(parent=link2.child, child=self.child_reused)
        link3 = LinkFactory(parent=self.tree.root_node)
        link3_1 = LinkFactory(parent=link3.child, child=self.child_reused)

        result = self.tree.get_first_link_occurence_using_node(self.child_reused)
        error_msg = "Must take the first occurence from the order displayed in the tree"
        self.assertEqual(result, link1_1, error_msg)
        self.assertNotEqual(result, link2_1, error_msg)
        self.assertNotEqual(result, link3_1, error_msg)


class TestGetGreaterBlockValue(SimpleTestCase):
    def test_when_tree_is_empty(self):
        tree = ProgramTreeFactory()
        self.assertEqual(0, tree.get_greater_block_value())

    def test_when_1_link_without_block_value(self):
        tree = ProgramTreeFactory()
        LinkFactory(parent=tree.root_node, block=None)
        self.assertEqual(0, tree.get_greater_block_value())

    def test_when_multiple_links_with_multiple_values(self):
        tree = ProgramTreeFactory()
        LinkFactory(parent=tree.root_node, block=13)
        LinkFactory(parent=tree.root_node, block=None)
        LinkFactory(parent=tree.root_node, block=1)
        LinkFactory(parent=tree.root_node, block=456)
        LinkFactory(parent=tree.root_node, block=123)
        self.assertEqual(6, tree.get_greater_block_value())


class TestCopyAndPrune(SimpleTestCase):

    def setUp(self):
        self.auth_relations = [AuthorizedRelationshipFactory()]

        self.original_root = NodeEducationGroupYearFactory()

        self.original_link = LinkFactory(parent=self.original_root, block=0)

        self.original_tree = ProgramTreeFactory(
            root_node=self.original_root,
            authorized_relationships=self.auth_relations
        )

    def test_should_copy_nodes(self):
        copied_tree = self.original_tree.prune()
        copied_root = copied_tree.root_node
        self.assertEqual(copied_root.node_id, self.original_root.node_id)
        self.assertEqual(copied_root.title, self.original_root.title)
        original_title = self.original_root.title
        copied_root.title = "Another value"
        self.assertEqual(copied_root.title, "Another value")
        self.assertEqual(self.original_root.title, original_title)

    def test_should_copy_tree(self):
        copied_tree = self.original_tree.prune()
        self.assertEqual(copied_tree.root_node, self.original_tree.root_node)
        self.assertEqual(copied_tree.authorized_relationships, self.original_tree.authorized_relationships)
        self.assertNotEqual(id(self.original_tree), id(copied_tree))

    def test_should_copy_links(self):
        original_link = self.original_tree.root_node.children[0]
        copied_tree = self.original_tree.prune()
        copied_link = copied_tree.root_node.children[0]
        self.assertEqual(copied_link.child, original_link.child)
        self.assertEqual(copied_link.parent, original_link.parent)
        self.assertEqual(copied_link.block, original_link.block)

        self.assertNotEqual(id(original_link), id(copied_link))
        self.assertNotEqual(id(original_link.child), id(copied_link.child))

        copied_link.block = 123456
        self.assertEqual(copied_link.block, 123456)
        self.assertNotEqual(original_link, 123456)

    def test_when_change_tree_signature(self):
        original_signature = ['self', 'root_node', 'authorized_relationships']
        current_signature = list(inspect.signature(ProgramTree.__init__).parameters.keys())
        error_msg = "Please update the {} function to fit with new object signature.".format(ProgramTree.prune)
        self.assertEqual(original_signature, current_signature, error_msg)

    def test_pruning_with_param_ignore_children_from(self):
        link = LinkFactory(parent=self.original_root)
        copied_tree = self.original_tree.prune(ignore_children_from={link.parent.node_type})
        self.assertListEqual([], copied_tree.root_node.children)

    def test_pruning_multiple_levels_with_param_ignore_children_from(self):
        link_1 = LinkFactory(
            parent__node_type=TrainingType.BACHELOR,
            child__node_type=GroupType.MINOR_LIST_CHOICE
        )
        link1_1 = LinkFactory(parent=link_1.child, child__node_type=GroupType.SUB_GROUP)
        link1_1_1 = LinkFactory(parent=link1_1.child)
        link1_1_1_1 = LinkFactory(parent=link1_1_1.child)
        original_tree = ProgramTreeFactory(root_node=link_1.parent)
        copied_tree = original_tree.prune(ignore_children_from={GroupType.SUB_GROUP})
        result = copied_tree.get_all_links()
        copied_link_1_1_1 = copied_tree.root_node.children[0].child.children[0].child
        self.assertListEqual([], copied_link_1_1_1.children)
        self.assertNotIn(link1_1_1, result)
        self.assertNotIn(link1_1_1_1, result)

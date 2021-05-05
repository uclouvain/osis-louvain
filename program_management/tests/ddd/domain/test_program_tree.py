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
import copy
import inspect

from django.test import SimpleTestCase

from base.ddd.utils.validation_message import MessageLevel
from base.models.enums.education_group_types import TrainingType, GroupType
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.domain.program_tree import build_path
from program_management.ddd.validators import validators_by_business_action
from program_management.models.enums import node_type
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipObjectFactory
from program_management.tests.ddd.factories.domain.prerequisite.prerequisite import PrerequisitesFactory
from program_management.tests.ddd.factories.domain.program_tree_version.training.OSIS2M import OSIS2MFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.service.mixins import ValidatorPatcherMixin
from testing.testcases import DDDTestCase


class TestGetNodeByIdAndTypeProgramTree(SimpleTestCase):
    def setUp(self):
        link = LinkFactory(child=NodeGroupYearFactory(node_id=1))
        self.root_node = link.parent
        self.subgroup_node = link.child

        link_with_learning_unit = LinkFactory(parent=self.root_node, child=NodeLearningUnitYearFactory(node_id=1))
        self.learning_unit_node = link_with_learning_unit.child

        self.tree = ProgramTreeFactory(root_node=self.root_node)

    def test_should_return_None_when_no_node_present_with_corresponding_node_id(self):
        result = self.tree.get_node_by_id_and_type(2, node_type.NodeType.LEARNING_UNIT)
        self.assertIsNone(result)

    def test_should_return_node_matching_specific_node_id_with_respect_to_class(self):
        result = self.tree.get_node_by_id_and_type(1, node_type.NodeType.LEARNING_UNIT)
        self.assertEqual(
            result,
            self.learning_unit_node
        )

        result = self.tree.get_node_by_id_and_type(1, node_type.NodeType.GROUP)
        self.assertEqual(
            result,
            self.subgroup_node
        )


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
        self.auth_relations = [AuthorizedRelationshipObjectFactory()]

        self.original_root = NodeGroupYearFactory()

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
        self.assertNotEqual(original_link.block, 123456)

    def test_when_change_tree_signature(self):
        original_signature = ['self', 'root_node', 'authorized_relationships', 'entity_id', 'prerequisites', 'report']
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


class TestGetNodesThatHavePrerequisites(SimpleTestCase):

    def setUp(self) -> None:
        self.link_with_root = LinkFactory(parent__title='ROOT', child__title='child_ROOT')
        self.link_with_child = LinkFactory(
            parent=self.link_with_root.child,
            child=NodeLearningUnitYearFactory(common_title_fr="child__child__ROOT",
                                              year=self.link_with_root.parent.year),
        )
        self.tree = ProgramTreeFactory(root_node=self.link_with_root.parent)

    def test_when_tree_has_not_node_that_have_prerequisites(self):
        self.assertEqual(self.tree.get_nodes_that_have_prerequisites(), [])

    def test_when_tree_has_node_that_have_prerequisites(self):
        tree = copy.deepcopy(self.tree)
        node_having_prerequisite = self.link_with_child.child
        PrerequisitesFactory.produce_inside_tree(
            context_tree=tree,
            node_having_prerequisite=node_having_prerequisite.entity_id,
            nodes_that_are_prequisites=[NodeLearningUnitYearFactory()]
        )
        result = tree.get_nodes_that_have_prerequisites()
        self.assertEqual(result, [node_having_prerequisite])


class TestGetCodesPermittedAsPrerequisite(SimpleTestCase):

    def setUp(self):
        self.tree = ProgramTreeFactory()

    def test_when_tree_contains_learning_units(self):
        link_with_learn_unit = LinkFactory(parent=self.tree.root_node, child=NodeLearningUnitYearFactory())
        link_with_group = LinkFactory(parent=self.tree.root_node, child=NodeGroupYearFactory())
        result = self.tree.get_nodes_permitted_as_prerequisite()
        expected_result = [link_with_learn_unit.child]
        self.assertListEqual(result, expected_result)
        self.assertNotIn(link_with_group.child, result)

    def test_when_tree_contains_only_groups(self):
        link_with_group1 = LinkFactory(parent=self.tree.root_node, child=NodeGroupYearFactory())
        link_with_group2 = LinkFactory(parent=self.tree.root_node, child=NodeGroupYearFactory())
        result = self.tree.get_nodes_permitted_as_prerequisite()
        expected_result = []
        self.assertListEqual(result, expected_result)

    def test_list_ordered_by_code(self):
        link_with_learn_unit1 = LinkFactory(parent=self.tree.root_node, child=NodeLearningUnitYearFactory(code='c2'))
        link_with_learn_unit2 = LinkFactory(parent=self.tree.root_node, child=NodeLearningUnitYearFactory(code='c1'))
        link_with_learn_unit3 = LinkFactory(parent=self.tree.root_node, child=NodeLearningUnitYearFactory(code='c3'))
        result = self.tree.get_nodes_permitted_as_prerequisite()
        expected_result_order = [link_with_learn_unit2.child, link_with_learn_unit1.child, link_with_learn_unit3.child]
        self.assertListEqual(result, expected_result_order)

    def test_when_node_is_used_inside_minor_and_inside_the_bachelor(self):
        tree = ProgramTreeFactory(root_node__node_type=TrainingType.BACHELOR)
        minor = NodeGroupYearFactory()
        ue = NodeLearningUnitYearFactory()

        LinkFactory(
            parent=tree.root_node,
            child=LinkFactory(
                parent=minor,
                child=ue
            ).parent
        )
        LinkFactory(parent=tree.root_node, child=ue)

        result = tree.get_nodes_permitted_as_prerequisite()
        expected_result = [ue]
        self.assertListEqual(result, expected_result)


class TestSetPrerequisite(SimpleTestCase, ValidatorPatcherMixin):
    def setUp(self):
        self.year = 2020
        self.tree = ProgramTreeFactory(root_node__year=self.year)
        self.link1 = LinkFactory(parent=self.tree.root_node, child=NodeLearningUnitYearFactory(year=self.year))
        LinkFactory(parent=self.tree.root_node, child=NodeLearningUnitYearFactory(code='LOSIS1452', year=self.year))
        LinkFactory(parent=self.tree.root_node, child=NodeLearningUnitYearFactory(code='MARC2589', year=self.year))

    def test_should_not_set_prerequisites_when_clean_is_not_valid(self):
        self.mock_validator(
            validators_by_business_action.UpdatePrerequisiteValidatorList,
            ["error_message_text"],
            level=MessageLevel.ERROR
        )
        self.tree.set_prerequisite("LOSIS1452 OU MARC2589", self.link1.child)
        self.assertTrue(len(self.tree.get_all_prerequisites()) == 0)

    def test_should_set_prerequisites_when_clean_is_valid(self):
        self.mock_validator(
            validators_by_business_action.UpdatePrerequisiteValidatorList,
            ["success_message_text"],
            level=MessageLevel.SUCCESS
        )
        self.tree.set_prerequisite("LOSIS1452 OU MARC2589", self.link1.child)
        self.assertTrue(len(self.tree.get_all_prerequisites()) == 1)


class TestGetIndirectParents(DDDTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.program_tree = OSIS2MFactory(year=2020, end_year=2020)[0].get_tree()

    def test_when_child_node_not_in_tree(self):
        child_node = NodeLearningUnitYearFactory()
        result = self.program_tree.search_indirect_parents(child_node)
        expected_result = []
        self.assertEqual(result, expected_result)

    def test_when_child_node_is_himself_an_indirect_parent(self):
        indirect_parent = next(n for n in self.program_tree.get_all_nodes() if n.is_finality())
        result = self.program_tree.search_indirect_parents(indirect_parent)
        expected_result = [self.program_tree.root_node]
        self.assertEqual(result, expected_result, "The indirect parent of a finality is the master 2M")

    def test_when_child_node_has_one_indirect_parent(self):
        child_node = next(n for n in self.program_tree.get_all_nodes() if n.is_finality_list_choice())
        result = self.program_tree.search_indirect_parents(child_node)
        expected_result = [self.program_tree.root_node]
        self.assertEqual(result, expected_result, "The indirect parent of a finality list choice is the master 2M")

    def test_when_child_node_has_one_indirect_parent_which_has_one_indirect_parent(self):
        child_node = NodeLearningUnitYearFactory()
        finality = next(n for n in self.program_tree.get_all_nodes() if n.is_finality())
        finality.add_child(child_node)
        result = self.program_tree.search_indirect_parents(child_node)
        expected_result = [finality]
        self.assertEqual(result, expected_result)
        self.assertNotIn(
            self.program_tree.root_node,
            expected_result,
            "Should not take the indirect parent (master 2M) of the first indirect parent (finality)"
        )

    def test_when_child_node_used_twice_in_tree_with_2_different_indirect_parent(self):
        child_node = NodeLearningUnitYearFactory()
        finality = next(n for n in self.program_tree.get_all_nodes() if n.is_finality())
        finality.add_child(child_node)  # Indirect parent is finality
        common_core = self.program_tree.get_node_by_code_and_year("LOSIS200M", self.program_tree.entity_id.year)
        common_core.add_child(child_node)  # Indirect parent is master 2M

        result = self.program_tree.search_indirect_parents(child_node)
        expected_result = [self.program_tree.root_node, finality]
        self.assertCountEqual(
            result,
            expected_result,
            "The learning unit Node is used in the common core (which is in the master 2M) AND in the finality"
        )

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
import mock
from django.test import TestCase

from base.models.enums import prerequisite_operator
from base.models.enums.link_type import LinkTypes
from base.models.enums.proposal_type import ProposalType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from program_management.ddd.domain import prerequisite
from program_management.ddd.domain import program_tree, node
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionNotFoundException, ProgramTreeVersion
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.ddd.repositories import load_tree
from django.utils.translation import gettext_lazy as _

VERSION_NAME = 'CEMS'
EDY_ACRONYM = 'CHIM1BA'


class TestLoadTree(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
            (education_group_version)
            root_node
            |-link_level_1
              |-link_level_2
                |-- leaf
        """
        cls.root_node = ElementGroupYearFactory()
        cls.link_level_1 = GroupElementYearFactory(parent_element=cls.root_node)
        cls.link_level_2 = GroupElementYearChildLeafFactory(parent_element=cls.link_level_1.child_element)
        cls.education_group_version = EducationGroupVersionFactory(
            root_group=cls.root_node.group_year
        )

    def test_case_tree_root_not_exist(self):
        unknown_tree_root_id = -1
        with self.assertRaises(node.NodeNotFoundException):
            load_tree.load(unknown_tree_root_id)

    def test_fields_to_load(self):
        group_year = self.root_node.group_year
        tree = load_tree.load(self.root_node.pk)
        self.assertEqual(tree.root_node.credits, group_year.credits, "Field used to load prerequisites excel")

    def test_case_tree_root_with_multiple_level(self):
        education_group_program_tree = load_tree.load(self.root_node.pk)
        self.assertIsInstance(education_group_program_tree, program_tree.ProgramTree)

        self.assertIsInstance(education_group_program_tree.root_node, node.NodeGroupYear)
        self.assertEqual(len(education_group_program_tree.root_node.children), 1)
        self.assertEqual(
            education_group_program_tree.root_node.children[0].child.title,
            self.link_level_1.child_element.group_year.acronym
        )

    # TODO : move this into test_load_prerequisite
    def test_case_load_tree_leaf_have_some_prerequisites(self):
        PrerequisiteFactory(
            education_group_version=self.education_group_version,
            learning_unit_year=self.link_level_2.child_element.learning_unit_year,
            items__groups=(
                (
                    LearningUnitYearFactory(
                        acronym='LDROI1200',
                        academic_year=self.link_level_2.child_element.learning_unit_year.academic_year
                    ),
                ),
                (
                    LearningUnitYearFactory(
                        acronym='LAGRO1600',
                        academic_year=self.link_level_2.child_element.learning_unit_year.academic_year
                    ),
                    LearningUnitYearFactory(
                        acronym='LBIR2300',
                        academic_year=self.link_level_2.child_element.learning_unit_year.academic_year
                    )
                )
            )
        )

        education_group_program_tree = load_tree.load(self.root_node.pk)
        leaf = education_group_program_tree.root_node.children[0].child.children[0].child

        self.assertIsInstance(leaf, node.NodeLearningUnitYear)
        self.assertIsInstance(leaf.prerequisite, prerequisite.Prerequisite)
        expected_str = 'LDROI1200 {AND} (LAGRO1600 {OR} LBIR2300)'.format(
            OR=_(prerequisite_operator.OR),
            AND=_(prerequisite_operator.AND)
        )
        self.assertEqual(str(leaf.prerequisite), expected_str)
        self.assertTrue(leaf.has_prerequisite)

    def test_case_load_tree_leaf_is_prerequisites_of(self):
        new_link = GroupElementYearChildLeafFactory(parent_element=self.link_level_1.child_element)

        # Add prerequisite between two node
        PrerequisiteFactory(
            education_group_version=self.education_group_version,
            learning_unit_year=self.link_level_2.child_element.learning_unit_year,
            items__groups=((new_link.child_element.learning_unit_year,),)
        )

        education_group_program_tree = load_tree.load(self.root_node.pk)
        leaf = education_group_program_tree.root_node.children[0].child.children[1].child

        self.assertIsInstance(leaf, node.NodeLearningUnitYear)
        self.assertIsInstance(leaf.is_prerequisite_of, list)
        self.assertEqual(len(leaf.is_prerequisite_of), 1)
        self.assertEqual(leaf.is_prerequisite_of[0].pk, self.link_level_2.child_element.pk)
        self.assertTrue(leaf.is_prerequisite)

    def test_case_load_tree_leaf_node_have_a_proposal(self):
        proposal_types = ProposalType.get_names()
        for p_type in proposal_types:
            proposal = ProposalLearningUnitFactory(
                learning_unit_year=self.link_level_2.child_element.learning_unit_year
            )
            with self.subTest(msg=p_type):
                proposal.type = p_type
                proposal.save()

                education_group_program_tree = load_tree.load(self.root_node.pk)
                leaf = education_group_program_tree.root_node.children[0].child.children[0].child
                self.assertTrue(leaf.has_proposal)
                self.assertEqual(leaf.proposal_type, p_type)

    def test_case_load_tree_leaf_node_have_no_proposal(self):
        education_group_program_tree = load_tree.load(self.root_node.pk)
        leaf = education_group_program_tree.root_node.children[0].child.children[0].child
        self.assertFalse(leaf.has_proposal)
        self.assertIsNone(leaf.proposal_type)


class TestLoadTreesFromChildren(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2020)
        cls.root_node = ElementGroupYearFactory(group_year__academic_year=cls.academic_year)
        cls.link_level_1 = GroupElementYearFactory(
            parent_element=cls.root_node,
            child_element__group_year__academic_year=cls.academic_year
        )
        cls.link_level_2 = GroupElementYearFactory(
            parent_element=cls.link_level_1.child_element,
            child_element__group_year__academic_year=cls.academic_year
        )

    def test_when_bad_arg(self):
        with self.assertRaises(Exception):
            load_tree.load_trees_from_children("I'm not a list arg")

    def test_when_child_list_is_empty(self):
        result = load_tree.load_trees_from_children([])
        self.assertEqual(result, [])

    def test_when_child_is_root(self):
        children_ids = [self.link_level_1.parent_element_id]
        result = load_tree.load_trees_from_children(children_ids)
        self.assertListEqual(result, [])

    def test_when_child_has_only_one_root_id(self):
        children_ids = [self.link_level_2.child_element_id]
        result = load_tree.load_trees_from_children(children_ids)
        expected_result = [load_tree.load(self.root_node.pk)]
        self.assertListEqual(result, expected_result)

    def test_when_child_is_learning_unit(self):
        link_level_3 = GroupElementYearChildLeafFactory(
            parent_element=self.link_level_2.child_element,
            child_element=ElementLearningUnitYearFactory(learning_unit_year__academic_year=self.academic_year)
        )
        children_ids = [link_level_3.child_element_id]
        result = load_tree.load_trees_from_children(children_ids)
        expected_result = [load_tree.load(self.root_node.pk)]
        self.assertListEqual(result, expected_result)

    def test_when_child_has_many_root_ids(self):
        root_node_2 = ElementGroupYearFactory(group_year__academic_year=self.academic_year)
        root_node_3 = ElementGroupYearFactory(group_year__academic_year=self.academic_year)
        child_element = self.link_level_2.child_element

        GroupElementYearFactory(parent_element=root_node_2, child_element=child_element)
        GroupElementYearFactory(parent_element=root_node_3, child_element=child_element)

        result = load_tree.load_trees_from_children([child_element.pk])
        expected_result = [
            load_tree.load(self.root_node.pk),
            load_tree.load(root_node_2.pk),
            load_tree.load(root_node_3.pk),
        ]
        self.assertEqual(len(result), len(expected_result))
        for tree in expected_result:
            self.assertIn(tree, result)

    def test_when_root_is_2_levels_up(self):
        child = self.link_level_2.child_element
        lvl1 = GroupElementYearFactory(
            parent_element__group_year__academic_year=child.group_year.academic_year,
            child_element=child
        )
        lvl2 = GroupElementYearFactory(
            parent_element__group_year__academic_year=child.group_year.academic_year,
            child_element=lvl1.parent_element
        )
        result = load_tree.load_trees_from_children([child.id])
        expected_parent = load_tree.load(lvl2.parent_element.id)
        self.assertNotIn(load_tree.load(lvl1.parent_element.id), result)
        self.assertIn(expected_parent, result)

    def test_when_link_type_is_reference(self):
        parent_node_type_reference = ElementGroupYearFactory(group_year__academic_year=self.academic_year)
        child = self.link_level_2.child_element
        GroupElementYearFactory(
            parent_element=parent_node_type_reference,
            child_element=child,
            link_type=LinkTypes.REFERENCE.name
        )
        result = load_tree.load_trees_from_children([child.id], link_type=LinkTypes.REFERENCE)
        expected_result = [load_tree.load(parent_node_type_reference.pk)]
        self.assertListEqual(result, expected_result)

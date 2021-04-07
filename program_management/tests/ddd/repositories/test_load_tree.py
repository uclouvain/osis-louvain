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
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.models.enums import prerequisite_operator
from base.models.enums.proposal_type import ProposalType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import TrainingEducationGroupTypeFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from program_management.ddd import command
from program_management.ddd.domain import prerequisite
from program_management.ddd.domain import program_tree, node
from program_management.ddd.domain.exception import ProgramTreeNotFoundException
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.ddd.service.read import get_program_tree_service
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory

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
        cls.academic_year = AcademicYearFactory(current=True)
        cls.root_node = ElementGroupYearFactory(group_year__academic_year=cls.academic_year)
        cls.link_level_1 = GroupElementYearFactory(
            parent_element=cls.root_node,
            child_element__group_year__academic_year=cls.academic_year,
        )
        cls.link_level_2 = GroupElementYearChildLeafFactory(
            parent_element=cls.link_level_1.child_element,
            child_element__learning_unit_year__academic_year=cls.academic_year
        )
        cls.education_group_version = EducationGroupVersionFactory(
            root_group=cls.root_node.group_year
        )

    def test_case_tree_root_not_exist(self):
        unknown_tree_root_id = -1
        with self.assertRaises(ProgramTreeNotFoundException):
            get_program_tree_service.get_program_tree_from_root_element_id(
                command.GetProgramTreeFromRootElementIdCommand(root_element_id=unknown_tree_root_id)
            )

    def test_fields_to_load(self):
        group_year = self.root_node.group_year
        tree = get_program_tree_service.get_program_tree_from_root_element_id(
            command.GetProgramTreeFromRootElementIdCommand(root_element_id=self.root_node.pk)
        )
        self.assertEqual(tree.root_node.credits, group_year.credits, "Field used to load prerequisites excel")
        self.assertEqual(tree.root_node.version_name, self.education_group_version.version_name)
        self.assertEqual(tree.root_node.version_title_fr, self.education_group_version.title_fr)
        self.assertEqual(tree.root_node.version_title_en, self.education_group_version.title_en)

    def test_case_tree_root_with_multiple_level(self):
        education_group_program_tree = get_program_tree_service.get_program_tree_from_root_element_id(
            command.GetProgramTreeFromRootElementIdCommand(root_element_id=self.root_node.pk)
        )
        self.assertIsInstance(education_group_program_tree, program_tree.ProgramTree)

        self.assertIsInstance(education_group_program_tree.root_node, node.NodeGroupYear)
        self.assertEqual(len(education_group_program_tree.root_node.children), 1)
        self.assertEqual(
            education_group_program_tree.root_node.children[0].child.title,
            self.link_level_1.child_element.group_year.acronym
        )

    # FIXME : move this into test_load_prerequisite
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
        education_group_program_tree = get_program_tree_service.get_program_tree_from_root_element_id(
            command.GetProgramTreeFromRootElementIdCommand(root_element_id=self.root_node.pk)
        )
        leaf = education_group_program_tree.root_node.children[0].child.children[0].child

        self.assertIsInstance(leaf, node.NodeLearningUnitYear)
        self.assertTrue(education_group_program_tree.has_prerequisites(leaf))
        result = education_group_program_tree.get_prerequisite(leaf)
        self.assertIsInstance(result, prerequisite.Prerequisite)
        expected_str = 'LDROI1200 {AND} (LAGRO1600 {OR} LBIR2300)'.format(
            OR=_(prerequisite_operator.OR),
            AND=_(prerequisite_operator.AND)
        )
        self.assertEqual(str(result), expected_str)

    def test_case_load_tree_leaf_is_prerequisites_of(self):
        new_link = GroupElementYearChildLeafFactory(
            parent_element=self.link_level_1.child_element,
            child_element__learning_unit_year__academic_year=self.academic_year
        )

        # Add prerequisite between two node
        learnin_unit_that_has_prerequisite = self.link_level_2.child_element.learning_unit_year
        PrerequisiteFactory(
            education_group_version=self.education_group_version,
            learning_unit_year=learnin_unit_that_has_prerequisite,
            items__groups=((new_link.child_element.learning_unit_year,),)
        )

        education_group_program_tree = get_program_tree_service.get_program_tree_from_root_element_id(
            command.GetProgramTreeFromRootElementIdCommand(root_element_id=self.root_node.pk)
        )
        leaf = education_group_program_tree.root_node.children[0].child.children[1].child

        self.assertIsInstance(leaf, node.NodeLearningUnitYear)
        is_prerequisite_of = education_group_program_tree.search_is_prerequisite_of(leaf)
        self.assertIsInstance(is_prerequisite_of, list)
        self.assertEqual(len(is_prerequisite_of), 1)
        self.assertEqual(is_prerequisite_of[0].code, learnin_unit_that_has_prerequisite.acronym)
        self.assertEqual(is_prerequisite_of[0].year, learnin_unit_that_has_prerequisite.academic_year.year)
        self.assertTrue(education_group_program_tree.is_prerequisite(leaf))

    def test_case_load_tree_leaf_node_have_a_proposal(self):
        proposal_types = ProposalType.get_names()
        for p_type in proposal_types:
            proposal = ProposalLearningUnitFactory(
                learning_unit_year=self.link_level_2.child_element.learning_unit_year
            )
            with self.subTest(msg=p_type):
                proposal.type = p_type
                proposal.save()

                education_group_program_tree = get_program_tree_service.get_program_tree_from_root_element_id(
                    command.GetProgramTreeFromRootElementIdCommand(root_element_id=self.root_node.pk)
                )
                leaf = education_group_program_tree.root_node.children[0].child.children[0].child
                self.assertTrue(leaf.has_proposal)
                self.assertEqual(leaf.proposal_type, p_type)

    def test_case_load_tree_leaf_node_have_no_proposal(self):
        education_group_program_tree = get_program_tree_service.get_program_tree_from_root_element_id(
            command.GetProgramTreeFromRootElementIdCommand(root_element_id=self.root_node.pk)
        )
        leaf = education_group_program_tree.root_node.children[0].child.children[0].child
        self.assertFalse(leaf.has_proposal)
        self.assertIsNone(leaf.proposal_type)

    def test_when_load_tree_root_ids_contained_each_others(self):
        """
        Test the load multiple trees function and ensure that the trees are correctly loaded
        even if we ask to load 2 trees where the first tree is a child of the second tree
        """
        node_contained_in_training = self.root_node

        training_containing_root_node = ElementGroupYearFactory(
            group_year__education_group_type=TrainingEducationGroupTypeFactory(),
            group_year__partial_acronym='LMIN1111',
            group_year__academic_year=self.academic_year,
        )

        GroupElementYearFactory(
            parent_element=training_containing_root_node,
            child_element=node_contained_in_training
        )

        root_ids_where_one_root_is_contained_into_the_second_root = [
            node_contained_in_training.pk, training_containing_root_node.pk
        ]
        result = ProgramTreeRepository.search(root_ids=root_ids_where_one_root_is_contained_into_the_second_root)
        self.assertTrue(len(result) == 2)
        first_root = result[0].root_node
        self.assertEqual(first_root.code, node_contained_in_training.group_year.partial_acronym)
        self.assertEqual(first_root.year, node_contained_in_training.group_year.academic_year.year)
        second_root = result[1].root_node
        self.assertEqual(second_root.code, training_containing_root_node.group_year.partial_acronym)
        self.assertEqual(second_root.year, training_containing_root_node.group_year.academic_year.year)

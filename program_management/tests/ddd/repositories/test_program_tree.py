# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django.test import TestCase
from mock import Mock

from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from program_management.ddd import command
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.repositories import program_tree
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory


class TestSearchTreesFromChildren(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_year = AcademicYearFactory()
        cls.link_1 = GroupElementYearFactory(
            parent_element__group_year__academic_year=academic_year,
            child_element__group_year__academic_year=academic_year
        )
        cls.link_1_1 = GroupElementYearFactory(
            parent_element=cls.link_1.child_element,
            child_element__group_year__academic_year=academic_year
        )
        cls.link_1_1_1 = GroupElementYearFactory(
            parent_element=cls.link_1_1.child_element,
            child_element__group_year__academic_year=academic_year
        )
        cls.link_1_2 = GroupElementYearFactory(
            parent_element=cls.link_1.child_element,
            child_element__group_year__academic_year=academic_year
        )
        cls.link_2 = GroupElementYearFactory(
            parent_element=cls.link_1.parent_element,
            child_element__group_year__academic_year=academic_year
        )

        cls.other_tree_link_1 = GroupElementYearFactory(
            parent_element__group_year__academic_year=academic_year,
            child_element__group_year__academic_year=academic_year
        )
        cls.other_tree_link_1_1 = GroupElementYearFactory(
            parent_element=cls.other_tree_link_1.child_element,
            child_element=cls.link_1_1_1.child_element
        )

    def test_should_return_list_of_one_tree_where_node_present_only_in_one_tree(self):
        node_identiy = NodeIdentity(
            code=self.link_2.child_element.group_year.partial_acronym,
            year=self.link_2.child_element.group_year.academic_year.year
        )
        expected_tree_identity = ProgramTreeIdentity(
            code=self.link_1.parent_element.group_year.partial_acronym,
            year=self.link_1.parent_element.group_year.academic_year.year
        )
        result = program_tree.ProgramTreeRepository.search_from_children([node_identiy])

        self.assertCountEqual(
            [tree.entity_id for tree in result],
            [expected_tree_identity]
        )

    def test_should_return_list_of_multiple_trees_where_node_present_only_in_multiple_trees(self):
        node_identiy = NodeIdentity(
            code=self.link_1_1_1.child_element.group_year.partial_acronym,
            year=self.link_1_1_1.child_element.group_year.academic_year.year
        )
        expected_tree_identities = [
            ProgramTreeIdentity(
                code=self.link_1.parent_element.group_year.partial_acronym,
                year=self.link_1.parent_element.group_year.academic_year.year
            ),
            ProgramTreeIdentity(
                code=self.other_tree_link_1.parent_element.group_year.partial_acronym,
                year=self.other_tree_link_1.parent_element.group_year.academic_year.year
            ),

        ]
        result = program_tree.ProgramTreeRepository.search_from_children([node_identiy])

        self.assertCountEqual(
            [tree.entity_id for tree in result],
            expected_tree_identities
        )


class TestDeleteProgramTree(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()

    def setUp(self) -> None:
        """
        |root_node (Training)
        |--- subgroup (Group)
           |---- mini_training (Mini-Training)
        """
        self.training_version = StandardEducationGroupVersionFactory(
            root_group__academic_year=self.academic_year,
            root_group__education_group_type__name=TrainingType.BACHELOR.name,
            offer__academic_year=self.academic_year,
            offer__education_group_type__name=TrainingType.BACHELOR.name,
        )
        self.root_node = ElementGroupYearFactory(group_year=self.training_version.root_group)
        self.subgroup = ElementGroupYearFactory(
            group_year__academic_year=self.academic_year,
            group_year__education_group_type__name=GroupType.SUB_GROUP.name
        )
        self.mini_training_version = StandardEducationGroupVersionFactory(
            root_group__academic_year=self.academic_year,
            root_group__education_group_type__name=MiniTrainingType.OPTION.name,
            offer__academic_year=self.academic_year,
            offer__education_group_type__name=MiniTrainingType.OPTION.name,
        )
        self.mini_training_element = ElementGroupYearFactory(group_year=self.mini_training_version.root_group)

        GroupElementYearFactory(parent_element=self.root_node, child_element=self.subgroup)
        GroupElementYearFactory(parent_element=self.subgroup, child_element=self.mini_training_element)

        self.program_tree_id = ProgramTreeIdentity(
            code=self.root_node.group_year.partial_acronym,
            year=self.root_node.group_year.academic_year.year
        )

    def test_assert_all_linked_are_removed(self):
        ProgramTreeRepository.delete(
            self.program_tree_id,
            delete_node_service=Mock(),
        )

        self.assertEqual(GroupElementYear.objects.all().count(), 0)

    def test_assert_called_right_cmd_service_according_to_node_type(self):
        mock_delete_node_service = Mock()

        ProgramTreeRepository.delete(
            self.program_tree_id,
            delete_node_service=mock_delete_node_service,
        )

        cmd_delete_group = command.DeleteNodeCommand(
            code=self.subgroup.group_year.partial_acronym,
            year=self.subgroup.group_year.academic_year.year,
            node_type=GroupType.SUB_GROUP.name
        )
        mock_delete_node_service.assert_any_call(cmd_delete_group)

        cmd_delete_training = command.DeleteNodeCommand(
            code=self.training_version.root_group.partial_acronym,
            year=self.training_version.root_group.academic_year.year,
            node_type=TrainingType.BACHELOR.name
        )
        mock_delete_node_service.assert_any_call(cmd_delete_training)

        cmd_delete_mini_training = command.DeleteNodeCommand(
            code=self.mini_training_version.root_group.partial_acronym,
            year=self.mini_training_version.root_group.academic_year.year,
            node_type=MiniTrainingType.OPTION.name
        )
        mock_delete_node_service.assert_any_call(cmd_delete_mini_training)

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

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.repositories import program_tree


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
            [tree.root_node.entity_id for tree in result],
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
            [tree.root_node.entity_id for tree in result],
            expected_tree_identities
        )

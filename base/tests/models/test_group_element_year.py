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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.db import IntegrityError
from django.test import TestCase

from base.models.enums.link_type import LinkTypes
from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from program_management.ddd.repositories import find_roots
from program_management.tests.factories.element import ElementGroupYearFactory


class TestSaveGroupElementYear(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()

    def test_simple_saves_ok(self):
        egy1 = EducationGroupYearFactory(academic_year=self.academic_year)
        egy2 = EducationGroupYearFactory(academic_year=self.academic_year)
        egy3 = EducationGroupYearFactory(academic_year=self.academic_year)

        GroupElementYearFactory(
            parent=egy2,
            child_branch=egy1,
        )
        GroupElementYearFactory(
            parent=egy3,
            child_branch=egy2,
        )

    def test_save_with_child_branch_and_child_leaf_ko(self):
        egy = EducationGroupYearFactory(academic_year=self.academic_year)
        luy = LearningUnitYearFactory()
        with self.assertRaises(IntegrityError):
            GroupElementYearFactory(
                parent=egy,
                child_branch=egy,
                child_leaf=luy,
            )


class TestManagerGetAdjacencyList(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_element_a = ElementGroupYearFactory()
        cls.level_1 = GroupElementYearFactory(parent_element=cls.root_element_a, order=0)
        cls.level_11 = GroupElementYearFactory(parent_element=cls.level_1.child_element, order=0)
        cls.level_2 = GroupElementYearFactory(parent_element=cls.root_element_a, order=1)

        cls.root_element_b = ElementGroupYearFactory()
        GroupElementYearFactory(parent_element=cls.root_element_b, order=0)

    def test_case_root_elements_ids_args_is_not_a_correct_instance(self):
        with self.assertRaises(Exception):
            GroupElementYear.objects.get_adjacency_list('bad_args')

    def test_case_root_elements_ids_is_empty(self):
        adjacency_list = GroupElementYear.objects.get_adjacency_list(root_elements_ids=[])
        self.assertEqual(len(adjacency_list), 0)

    def test_case_filter_by_root_elements_ids(self):
        adjacency_list = GroupElementYear.objects.get_adjacency_list([self.root_element_a.pk])
        self.assertEqual(len(adjacency_list), 3)

        expected_first_elem = {
            'starting_node_id': self.root_element_a.pk,
            'id': self.level_1.pk,
            'child_id': self.level_1.child_element_id,
            'parent_id': self.level_1.parent_element_id,
            'order': 0,
            'level': 0,
            'path': "|".join([str(self.level_1.parent_element_id), str(self.level_1.child_element_id)])
        }
        self.assertDictEqual(adjacency_list[0], expected_first_elem)

    def test_case_multiple_root_elements_ids(self):
        adjacency_list = GroupElementYear.objects.get_adjacency_list([self.root_element_a.pk, self.root_element_b.pk])
        self.assertEqual(len(adjacency_list), 4)


class TestManagerGetReverseAdjacencyList(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_element_a = ElementGroupYearFactory()
        cls.level_1 = GroupElementYearFactory(parent_element=cls.root_element_a)
        cls.level_11 = GroupElementYearFactory(parent_element=cls.level_1.child_element)
        cls.level_111 = GroupElementYearChildLeafFactory(parent_element=cls.level_11.child_element)
        cls.level_2 = GroupElementYearChildLeafFactory(parent_element=cls.root_element_a, order=5)

    def test_case_root_elements_ids_args_is_not_a_correct_instance(self):
        with self.assertRaises(Exception):
            GroupElementYear.objects.get_reverse_adjacency_list(child_element_ids='bad_args')

    def test_case_root_elements_ids_is_empty(self):
        reverse_adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(child_element_ids=[])
        self.assertEqual(len(reverse_adjacency_list), 0)

    def test_case_filter_by_child_ids(self):
        reverse_adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(
            child_element_ids=[self.level_2.child_element_id]
        )
        self.assertEqual(len(reverse_adjacency_list), 1)

        expected_first_elem = {
            'starting_node_id': self.level_2.child_element_id,
            'id': self.level_2.pk,
            'child_id': self.level_2.child_element_id,
            'parent_id': self.level_2.parent_element_id,
            'order': self.level_2.order,
            'level': 0,
        }
        self.assertDictEqual(reverse_adjacency_list[0], expected_first_elem)

    def test_case_multiple_child_ids(self):
        adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(child_element_ids=[
            self.level_2.child_element_id,
            self.level_111.child_element_id
        ])
        self.assertEqual(len(adjacency_list), 4)

    def test_case_child_is_education_group_instance(self):
        level_2bis = GroupElementYearFactory(
            parent_element=self.root_element_a,
            order=6
        )
        reverse_adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(
            child_element_ids=[level_2bis.child_element_id]
        )
        self.assertEqual(len(reverse_adjacency_list), 1)

    def test_case_filter_link_type(self):
        link_reference = GroupElementYearFactory(
            parent_element__group_year__academic_year=self.level_1.child_element.group_year.academic_year,
            child_element=self.level_1.child_element,
            order=6,
            link_type=LinkTypes.REFERENCE.name
        )
        link_not_reference = GroupElementYearFactory(
            parent_element__group_year__academic_year=self.level_1.child_element.group_year.academic_year,
            child_element=self.level_1.child_element,
            order=6,
            link_type=None
        )
        reverse_adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(
            child_element_ids=[self.level_1.child_element_id],
            link_type=LinkTypes.REFERENCE,
        )
        result_parent_ids = [rec['parent_id'] for rec in reverse_adjacency_list]
        self.assertIn(link_reference.parent_element_id, result_parent_ids)
        self.assertNotIn(link_not_reference.parent_element_id, result_parent_ids)


class TestManagerGetRoots(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.root_element_a = ElementGroupYearFactory(group_year__academic_year=cls.academic_year)
        cls.level_1 = GroupElementYearFactory(
            parent_element=cls.root_element_a,
            child_element__group_year__academic_year=cls.academic_year
        )
        cls.level_11 = GroupElementYearFactory(
            parent_element=cls.level_1.child_element,
            child_element__group_year__academic_year=cls.academic_year
        )
        cls.level_111 = GroupElementYearChildLeafFactory(
            parent_element=cls.level_11.child_element,
            child_element__learning_unit_year__academic_year=cls.academic_year
        )
        cls.level_2 = GroupElementYearFactory(
            parent_element=cls.root_element_a,
            child_element__group_year__education_group_type__group=True,
            child_element__group_year__academic_year=cls.academic_year,
            order=5
        )
        cls.level_21 = GroupElementYearChildLeafFactory(
            parent_element=cls.level_2.child_element,
            child_element__learning_unit_year__academic_year=cls.academic_year
        )
        cls.root_categories_name = [category.name for category in find_roots.DEFAULT_ROOT_CATEGORIES]

    def test_when_no_parameters_set_then_return_empty_list(self):
        child_root_list = GroupElementYear.objects.get_root_list(root_category_name=self.root_categories_name)
        self.assertEqual(len(child_root_list), 0)

    def test_when_empty_children_list_given_then_return_empty_list(self):
        child_root_list = GroupElementYear.objects.get_root_list(
            child_element_ids=[],
            root_category_name=self.root_categories_name
        )
        self.assertEqual(len(child_root_list), 0)

    def test_when_child_leaf_given_then_return_all_their_root(self):
        child_element_ids = [self.level_21.child_element_id]
        child_root_list = GroupElementYear.objects.get_root_list(
            child_element_ids=child_element_ids,
            root_category_name=self.root_categories_name
        )
        self.assertCountEqual(
            child_root_list,
            [{"child_id": self.level_21.child_element_id, "root_id": self.level_2.parent_element_id}]
        )

    def test_when_child_branch_given_then_return_all_their_root(self):
        child_element_ids = [self.level_11.child_element_id]
        child_root_list = GroupElementYear.objects.get_root_list(
            child_element_ids=child_element_ids,
            root_category_name=self.root_categories_name
        )
        self.assertCountEqual(
            child_root_list,
            [{"child_id": self.level_11.child_element_id, "root_id": self.level_11.parent_element_id}]
        )

    def test_when_academic_year_given_then_return_all_children_root_for_given_year(self):
        child_root_list = GroupElementYear.objects.get_root_list(
            academic_year_id=self.root_element_a.group_year.academic_year_id,
            root_category_name=self.root_categories_name
        )
        self.assertCountEqual(
            child_root_list,
            [{"child_id": self.level_1.child_element_id, "root_id": self.level_1.parent_element_id},
             {"child_id": self.level_11.child_element_id, "root_id": self.level_11.parent_element_id},
             {"child_id": self.level_111.child_element_id, "root_id": self.level_111.parent_element_id},
             {"child_id": self.level_2.child_element_id, "root_id": self.level_2.parent_element_id},
             {"child_id": self.level_21.child_element_id, "root_id": self.level_2.parent_element_id}]
        )

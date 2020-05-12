from unittest import mock

from django.test import TestCase

import program_management.ddd
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_types, education_group_categories
from base.models.enums.education_group_types import MiniTrainingType, GroupType
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory, GroupEducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


class TestFindAllRoots(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()

    def test_when_no_link_for_academic_year(self):
        result = program_management.ddd.repositories.find_roots.find_all_roots_for_academic_year(self.academic_year.id)
        self.assertDictEqual(result, {})

    def test_when_one_link_for_academic_year_should_but_do_not_match_criteria(self):
        GroupElementYearFactory(
            parent__education_group_type__group=True
        )
        result = program_management.ddd.repositories.find_roots.find_all_roots_for_academic_year(self.academic_year.id)
        self.assertDictEqual(result, {})

    def test_should_return_all_children_root_for_academic_year(self):
        GroupElementYearFactory(
            parent__academic_year=self.academic_year,
            child_branch__academic_year=self.academic_year
        )
        GroupElementYearChildLeafFactory(
            parent__academic_year=self.academic_year,
            child_leaf__academic_year=self.academic_year
        )
        GroupElementYearChildLeafFactory(
            parent__academic_year=self.academic_year,
            child_leaf__academic_year=self.academic_year
        )
        result = program_management.ddd.repositories.find_roots.find_all_roots_for_academic_year(self.academic_year.id)
        self.assertEqual(
            len(result),
            3
        )


class TestFindRelatedRootEducationGroups(TestCase):
    """Unit tests for find_learning_unit_roots() function"""

    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.child_leaf = LearningUnitYearFactory(academic_year=cls.current_academic_year)

        root_group_type = EducationGroupTypeFactory(
            name=education_group_types.TrainingType.BACHELOR.name,
            category=education_group_categories.TRAINING
        )
        cls.root = EducationGroupYearFactory(academic_year=cls.current_academic_year,
                                             education_group_type=root_group_type)

    @mock.patch('program_management.ddd.repositories.find_roots._assert_same_academic_year')
    def test_objects_instances_check_is_called(self, mock_check_instance):
        program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        self.assertTrue(mock_check_instance.called)

    def test_case_filters_arg_is_none(self):
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        self.assertEqual(
            result[self.child_leaf.id],
            []
        )

    def test_with_filters_case_direct_parent_id_root_and_matches_filters(self):
        element_year = GroupElementYearFactory(parent=self.root, child_branch=None, child_leaf=self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        expected_result = {
            self.child_leaf.id: [element_year.parent.id]
        }
        self.assertEqual(result, expected_result)

    def test_with_filters_case_childs_with_different_academic_years(self):
        child_leaf_other_ac_year = LearningUnitYearFactory(
            academic_year=AcademicYearFactory(year=self.current_academic_year.year - 1)
        )
        with self.assertRaises(AttributeError):
            program_management.ddd.repositories.find_roots.find_roots([self.child_leaf, child_leaf_other_ac_year])

    def test_with_filters_case_direct_parent_is_root_and_not_matches_filter(self):
        root = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(
                name=education_group_types.GroupType.OPTION_LIST_CHOICE.name,
                category=education_group_categories.GROUP
            )
        )
        GroupElementYearFactory(parent=root, child_branch=None, child_leaf=self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        self.assertEqual(
            result[self.child_leaf.id],
            []
        )

    def test_with_filters_case_root_in_2nd_level_and_direct_parent_matches_filter(self):
        root = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MA_120.name,
                category=education_group_categories.TRAINING
            )
        )
        child_branch = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MD_120.name,
                category=education_group_categories.TRAINING
            )
        )
        GroupElementYearFactory(parent=root, child_branch=child_branch)
        GroupElementYearFactory(parent=child_branch, child_branch=None, child_leaf=self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        expected_result = {
            self.child_leaf.id: [child_branch.id]
        }
        self.assertDictEqual(result, expected_result)
        self.assertNotIn(root.id, result)

    def test_when_exclude_root_categories_is_set(self):
        root = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MA_120.name,
                category=education_group_categories.TRAINING
            )
        )
        child_branch = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MD_120.name,
                category=education_group_categories.TRAINING
            )
        )
        GroupElementYearFactory(parent=root, child_branch=child_branch)
        GroupElementYearFactory(parent=child_branch, child_branch=None, child_leaf=self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots(
            [self.child_leaf],
            exclude_root_categories=[education_group_types.TrainingType.MASTER_MD_120]
        )
        expected_result = {
            self.child_leaf.id: [root.id]
        }
        self.assertDictEqual(result, expected_result)
        self.assertNotIn(root.id, result)

    def test_with_filters_case_multiple_parents_in_2nd_level(self):
        root_2 = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MA_120.name,
                category=education_group_categories.TRAINING
            )
        )
        child_branch = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=GroupEducationGroupTypeFactory()
        )
        GroupElementYearFactory(parent=self.root, child_branch=child_branch)
        GroupElementYearFactory(parent=root_2, child_branch=child_branch)
        GroupElementYearFactory(parent=child_branch, child_branch=None, child_leaf=self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        self.assertCountEqual(
            result[self.child_leaf.id],
            [self.root.id, root_2.id]
        )

    def test_when_parent_of_parents_is_set(self):
        root_2 = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MA_120.name,
                category=education_group_categories.TRAINING
            )
        )
        child_branch = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
        )
        GroupElementYearFactory(parent=self.root, child_branch=child_branch)
        GroupElementYearFactory(parent=root_2, child_branch=child_branch)
        GroupElementYearFactory(parent=child_branch, child_branch=None, child_leaf=self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots(
            [self.child_leaf],
            as_instances=True,
            with_parents_of_parents=True,
        )
        self.assertCountEqual(
            result[self.child_leaf.id],
            [child_branch]
        )
        self.assertCountEqual(
            result[child_branch.id],
            [root_2, self.root]
        )

    def test_with_filters_case_objects_are_education_group_instance(self):
        root = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
        )
        child_branch = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
        )
        GroupElementYearFactory(parent=root, child_branch=child_branch)
        result = program_management.ddd.repositories.find_roots.find_roots([child_branch])
        expected_result = {
            child_branch.id: [root.id]
        }
        self.assertDictEqual(result, expected_result)


class TestFindLearningUnitFormationRoots(TestCase):
    """Unit tests for find_learning_unit_formation_roots()"""

    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.child_leaf = LearningUnitYearFactory(academic_year=cls.current_academic_year)

    @staticmethod
    def _build_hierarchy(academic_year, direct_parent_type, child_leaf):
        group_element_child = GroupElementYearFactory(
            parent=EducationGroupYearFactory(academic_year=academic_year, education_group_type=direct_parent_type),
            child_branch=None,
            child_leaf=child_leaf
        )
        group_element_root = GroupElementYearFactory(
            parent=EducationGroupYearFactory(academic_year=academic_year),
            child_branch=group_element_child.parent,
        )
        return locals()

    def test_group_type_option_is_correctly_excluded(self):
        type_option = EducationGroupTypeFactory(
            name=MiniTrainingType.OPTION.name,
            category=education_group_categories.MINI_TRAINING
        )
        hierarchy = self._build_hierarchy(self.current_academic_year, type_option, self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])

    def test_all_group_types_of_category_mini_training_stops_recursivity(self):
        group_type = EducationGroupTypeFactory(category=education_group_categories.MINI_TRAINING)
        hierarchy = self._build_hierarchy(self.current_academic_year, group_type, self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])

    def test_all_group_types_of_category_training_stops_recursivity(self):
        type_bachelor = EducationGroupTypeFactory(
            name=education_group_types.TrainingType.BACHELOR.name,
            category=education_group_categories.TRAINING
        )
        hierarchy = self._build_hierarchy(self.current_academic_year, type_bachelor, self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])

    def test_case_group_category_is_not_root(self):
        a_group_type = EducationGroupTypeFactory(
            name=education_group_types.MiniTrainingType.OPTION.name,
            category=education_group_categories.GROUP)

        hierarchy = self._build_hierarchy(self.current_academic_year, a_group_type, self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])

    def test_case_group_category_is_root(self):
        a_group_type = EducationGroupTypeFactory(
            name=education_group_types.GroupType.SUB_GROUP.name,
            category=education_group_categories.GROUP
        )
        group_element = GroupElementYearFactory(
            parent=EducationGroupYearFactory(academic_year=self.current_academic_year,
                                             education_group_type=a_group_type),
            child_branch=None,
            child_leaf=self.child_leaf
        )
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_leaf])
        self.assertEqual(result[self.child_leaf.id], [])
        self.assertNotIn(group_element.parent.id, result[self.child_leaf.id])

    def test_case_arg_is_empty(self):
        result = program_management.ddd.repositories.find_roots.find_roots([])
        self.assertEqual(result, {})

    def test_with_kwarg_parents_as_instances_is_true(self):
        group_element = GroupElementYearFactory(
            child_branch=None,
            child_leaf=self.child_leaf
        )
        result = program_management.ddd.repositories.find_roots.find_roots(
            [self.child_leaf],
            as_instances=True,
        )
        self.assertEqual(result[self.child_leaf.id], [group_element.parent])

    def test_with_kwarg_is_root_when_matches_is_complementary_module_and_not_in_it(self):
        group_element = GroupElementYearFactory(
            child_branch=None,
            child_leaf=self.child_leaf
        )
        result = program_management.ddd.repositories.find_roots.find_roots(
            [self.child_leaf],
            additional_root_categories=[GroupType.COMPLEMENTARY_MODULE]
        )
        self.assertEqual(result[self.child_leaf.id], [group_element.parent.id])

    def test_with_kwarg_is_root_when_matches_is_complementary_module_and_in_it(self):
        group_type = EducationGroupTypeFactory(
            name=GroupType.COMPLEMENTARY_MODULE.name,
            category=education_group_categories.GROUP
        )
        hierarchy = self._build_hierarchy(self.current_academic_year, group_type, self.child_leaf)
        result = program_management.ddd.repositories.find_roots.find_roots(
            [self.child_leaf],
            additional_root_categories=[GroupType.COMPLEMENTARY_MODULE]
        )

        self.assertEqual(result[self.child_leaf.id], [hierarchy['group_element_child'].parent.id])


class TestConvertParentIdsToInstances(TestCase):
    """Unit tests for _convert_parent_ids_to_instances()"""

    def test_ids_correctly_converted_to_instances(self):
        group_element = GroupElementYearFactory(
            child_branch=None,
            child_leaf=LearningUnitYearFactory()
        )
        root_ids_by_object_id = program_management.ddd.repositories.find_roots.find_roots([group_element.child_leaf])
        result = program_management.ddd.repositories.find_roots._convert_parent_ids_to_instances(root_ids_by_object_id)
        expected_result = {
            group_element.child_leaf.id: [group_element.parent]
        }
        self.assertDictEqual(result, expected_result)
        self.assertIsInstance(list(result.keys())[0], int)
        self.assertIsInstance(result[group_element.child_leaf.id][0], EducationGroupYear)

    def test_ordered_by_acronym(self):
        learn_unit_year = LearningUnitYearFactory()
        group_element1 = GroupElementYearFactory(
            parent=EducationGroupYearFactory(acronym='ECGE1BA'),
            child_branch=None,
            child_leaf=learn_unit_year
        )
        group_element2 = GroupElementYearFactory(
            parent=EducationGroupYearFactory(acronym='DROI1BA'),
            child_branch=None,
            child_leaf=learn_unit_year
        )
        group_element3 = GroupElementYearFactory(
            parent=EducationGroupYearFactory(acronym='SPOL2MS/G'),
            child_branch=None,
            child_leaf=learn_unit_year
        )
        root_ids_by_object_id = program_management.ddd.repositories.find_roots.find_roots([learn_unit_year])
        result = program_management.ddd.repositories.find_roots._convert_parent_ids_to_instances(root_ids_by_object_id)
        expected_order = [group_element2.parent, group_element1.parent, group_element3.parent]
        self.assertListEqual(result[learn_unit_year.id], expected_order)


class TestAssertSameObjectsClass(TestCase):
    def test_case_unothorized_instance(self):
        with self.assertRaises(AttributeError):
            program_management.ddd.repositories.find_roots._assert_same_objects_class([AcademicYearFactory()])

    def test_case_different_objects_instances(self):
        with self.assertRaises(AttributeError):
            program_management.ddd.repositories.find_roots._assert_same_objects_class(
                [EducationGroupYearFactory(), LearningUnitYearFactory()])
from unittest import mock

from django.test import TestCase

import program_management.ddd
from base.models.enums import education_group_types, education_group_categories
from base.models.enums.education_group_types import MiniTrainingType, GroupType, TrainingType
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory, GroupEducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from program_management.models.element import Element
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory


class TestFindAllRoots(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()

    def test_when_no_link_for_academic_year(self):
        result = program_management.ddd.repositories.find_roots.find_all_roots_for_academic_year(self.academic_year.id)
        self.assertDictEqual(result, {})

    def test_when_one_link_for_academic_year_should_but_do_not_match_criteria(self):
        GroupElementYearFactory(parent_element__group_year__education_group_type__group=True)

        result = program_management.ddd.repositories.find_roots.find_all_roots_for_academic_year(self.academic_year.id)
        self.assertDictEqual(result, {})

    def test_should_return_all_children_root_for_academic_year(self):
        GroupElementYearFactory(
            parent_element__group_year__education_group_type__name=TrainingType.BACHELOR.name,
            parent_element__group_year__academic_year=self.academic_year,
            child_element__group_year__academic_year=self.academic_year,
        )
        GroupElementYearChildLeafFactory(
            parent_element__group_year__education_group_type__name=TrainingType.CAPAES.name,
            parent_element__group_year__academic_year=self.academic_year,
            child_element__learning_unit_year__academic_year=self.academic_year
        )
        GroupElementYearChildLeafFactory(
            parent_element__group_year__education_group_type__name=TrainingType.JUNIOR_YEAR.name,
            parent_element__group_year__academic_year=self.academic_year,
            child_element__learning_unit_year__academic_year=self.academic_year
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
        cls.child_element = ElementLearningUnitYearFactory(
            learning_unit_year__academic_year=cls.current_academic_year
        )

        root_group_type = EducationGroupTypeFactory(
            name=education_group_types.TrainingType.BACHELOR.name,
            category=education_group_categories.TRAINING
        )
        cls.root = ElementGroupYearFactory(
            group_year__academic_year=cls.current_academic_year,
            group_year__education_group_type=root_group_type
        )

    @mock.patch('program_management.ddd.repositories.find_roots._assert_same_academic_year')
    def test_assert_check_on_academic_year_of_object_is_called(self, mock_check_instance):
        program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        self.assertTrue(mock_check_instance.called)

    def test_case_filters_arg_is_none(self):
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        self.assertEqual(
            result[self.child_element.pk],
            []
        )

    def test_with_filters_case_direct_parent_id_root_and_matches_filters(self):
        element_year = GroupElementYearFactory(parent_element=self.root, child_element=self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        expected_result = {
            self.child_element.pk: [element_year.parent_element_id]
        }
        self.assertEqual(result, expected_result)

    def test_with_filters_case_childs_with_different_academic_years(self):
        child_element_other_ac_year = ElementLearningUnitYearFactory(
            learning_unit_year__academic_year__year=self.child_element.learning_unit_year.academic_year.year - 1
        )
        with self.assertRaises(AttributeError):
            program_management.ddd.repositories.find_roots.find_roots([self.child_element, child_element_other_ac_year])

    def test_with_filters_case_direct_parent_is_root_and_not_matches_filter(self):
        root_element = ElementGroupYearFactory(
            group_year__academic_year=self.current_academic_year,
            group_year__education_group_type=EducationGroupTypeFactory(
                name=education_group_types.GroupType.OPTION_LIST_CHOICE.name,
                category=education_group_categories.GROUP
            )
        )
        GroupElementYearFactory(parent_element=root_element, child_element=self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        self.assertEqual(
            result[self.child_element.pk],
            []
        )

    def test_with_filters_case_root_in_2nd_level_and_direct_parent_matches_filter(self):
        root_element = ElementGroupYearFactory(
            group_year__academic_year=self.current_academic_year,
            group_year__education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MA_120.name,
                category=education_group_categories.TRAINING
            )
        )
        finality_element = ElementGroupYearFactory(
            group_year__academic_year=self.current_academic_year,
            group_year__education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MD_120.name,
                category=education_group_categories.TRAINING
            )
        )
        GroupElementYearFactory(parent_element=root_element, child_element=finality_element)
        GroupElementYearFactory(parent_element=finality_element, child_element=self.child_element)

        result = program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        expected_result = {
            self.child_element.id: [finality_element.pk]
        }
        self.assertDictEqual(result, expected_result)
        self.assertNotIn(root_element.pk, result)

    def test_when_exclude_root_categories_is_set(self):
        root_element = ElementGroupYearFactory(
            group_year__academic_year=self.current_academic_year,
            group_year__education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MA_120.name,
                category=education_group_categories.TRAINING
            )
        )
        finality_element = ElementGroupYearFactory(
            group_year__academic_year=self.current_academic_year,
            group_year__education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MD_120.name,
                category=education_group_categories.TRAINING
            )
        )
        GroupElementYearFactory(parent_element=root_element, child_element=finality_element)
        GroupElementYearFactory(parent_element=finality_element, child_element=self.child_element)

        result = program_management.ddd.repositories.find_roots.find_roots(
            [self.child_element],
            exclude_root_categories=[education_group_types.TrainingType.MASTER_MD_120]
        )
        expected_result = {
            self.child_element.pk: [root_element.pk]
        }
        self.assertDictEqual(result, expected_result)
        self.assertNotIn(root_element.pk, result)

    def test_with_filters_case_multiple_parents_in_2nd_level(self):
        root_2_element = ElementGroupYearFactory(
            group_year__academic_year=self.current_academic_year,
            group_year__education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MA_120.name,
                category=education_group_categories.TRAINING
            )
        )
        group_element = ElementGroupYearFactory(
            group_year__academic_year=self.current_academic_year,
            group_year__education_group_type=GroupEducationGroupTypeFactory()
        )
        GroupElementYearFactory(parent_element=self.root, child_element=group_element)
        GroupElementYearFactory(parent_element=root_2_element, child_element=group_element)
        GroupElementYearFactory(parent_element=group_element, child_element=self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        self.assertCountEqual(
            result[self.child_element.pk],
            [self.root.pk, root_2_element.pk]
        )

    def test_when_parent_of_parents_is_set(self):
        root_2_element = ElementGroupYearFactory(
            group_year__academic_year=self.current_academic_year,
            group_year__education_group_type=EducationGroupTypeFactory(
                name=education_group_types.TrainingType.MASTER_MA_120.name,
                category=education_group_categories.TRAINING
            )
        )
        group_element = ElementGroupYearFactory(group_year__academic_year=self.current_academic_year)

        GroupElementYearFactory(parent_element=self.root, child_element=group_element)
        GroupElementYearFactory(parent_element=root_2_element, child_element=group_element)
        GroupElementYearFactory(parent_element=group_element, child_element=self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots(
            [self.child_element],
            as_instances=True,
            with_parents_of_parents=True,
        )
        self.assertCountEqual(
            result[self.child_element.pk],
            [group_element]
        )
        self.assertCountEqual(
            result[group_element.pk],
            [root_2_element, self.root]
        )

    def test_with_filters_case_objects_are_education_group_instance(self):
        root = ElementGroupYearFactory(group_year__academic_year=self.current_academic_year)
        group_element = ElementGroupYearFactory(group_year__academic_year=self.current_academic_year)

        GroupElementYearFactory(parent_element=root, child_element=group_element)
        result = program_management.ddd.repositories.find_roots.find_roots([group_element])
        expected_result = {
            group_element.pk: [root.pk]
        }
        self.assertDictEqual(result, expected_result)


class TestFindLearningUnitFormationRoots(TestCase):
    """Unit tests for find_learning_unit_formation_roots()"""

    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.child_element = ElementLearningUnitYearFactory(
            learning_unit_year__academic_year=cls.current_academic_year
        )

    @staticmethod
    def _build_hierarchy(academic_year, direct_parent_type, child_element):
        group_element_child = GroupElementYearChildLeafFactory(
            parent_element=ElementGroupYearFactory(
                group_year__academic_year=academic_year,
                group_year__education_group_type=direct_parent_type
            ),
            child_element=child_element
        )
        group_element_root = GroupElementYearFactory(
            parent_element=ElementGroupYearFactory(group_year__academic_year=academic_year),
            child_element=group_element_child.parent_element,
        )
        return locals()

    def test_group_type_option_is_correctly_excluded(self):
        type_option = EducationGroupTypeFactory(
            name=MiniTrainingType.OPTION.name,
            category=education_group_categories.MINI_TRAINING
        )
        hierarchy = self._build_hierarchy(self.current_academic_year, type_option, self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        self.assertNotIn(hierarchy['group_element_child'].parent_element_id, result[self.child_element.pk])
        self.assertIn(hierarchy['group_element_root'].parent_element_id, result[self.child_element.pk])

    def test_all_group_types_of_category_mini_training_stops_recursivity(self):
        group_type = EducationGroupTypeFactory(category=education_group_categories.MINI_TRAINING)
        hierarchy = self._build_hierarchy(self.current_academic_year, group_type, self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        self.assertNotIn(hierarchy['group_element_root'].parent_element_id, result[self.child_element.pk])
        self.assertIn(hierarchy['group_element_child'].parent_element_id, result[self.child_element.pk])

    def test_all_group_types_of_category_training_stops_recursivity(self):
        type_bachelor = EducationGroupTypeFactory(
            name=education_group_types.TrainingType.BACHELOR.name,
            category=education_group_categories.TRAINING
        )
        hierarchy = self._build_hierarchy(self.current_academic_year, type_bachelor, self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        self.assertNotIn(hierarchy['group_element_root'].parent_element_id, result[self.child_element.pk])
        self.assertIn(hierarchy['group_element_child'].parent_element_id, result[self.child_element.pk])

    def test_case_group_category_is_not_root(self):
        a_group_type = EducationGroupTypeFactory(
            name=education_group_types.MiniTrainingType.OPTION.name,
            category=education_group_categories.GROUP
        )

        hierarchy = self._build_hierarchy(self.current_academic_year, a_group_type, self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        self.assertNotIn(hierarchy['group_element_child'].parent_element_id, result[self.child_element.pk])
        self.assertIn(hierarchy['group_element_root'].parent_element_id, result[self.child_element.pk])

    def test_case_group_category_is_root(self):
        a_group_type = EducationGroupTypeFactory(
            name=education_group_types.GroupType.SUB_GROUP.name,
            category=education_group_categories.GROUP
        )
        group_element = GroupElementYearFactory(
            parent_element=ElementGroupYearFactory(
                group_year__academic_year=self.current_academic_year,
                group_year__education_group_type=a_group_type
            ),
            child_element=self.child_element
        )
        result = program_management.ddd.repositories.find_roots.find_roots([self.child_element])
        self.assertEqual(result[self.child_element.pk], [])
        self.assertNotIn(group_element.parent_element_id, result[self.child_element.pk])

    def test_case_arg_is_empty(self):
        result = program_management.ddd.repositories.find_roots.find_roots([])
        self.assertEqual(result, {})

    def test_with_kwarg_parents_as_instances_is_true(self):
        group_element = GroupElementYearChildLeafFactory(child_element=self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots(
            [self.child_element],
            as_instances=True,
        )
        self.assertEqual(result[self.child_element.pk], [group_element.parent_element])

    def test_with_kwarg_is_root_when_matches_is_complementary_module_and_not_in_it(self):
        group_element = GroupElementYearChildLeafFactory(child_element=self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots(
            [self.child_element],
            additional_root_categories=[GroupType.COMPLEMENTARY_MODULE]
        )
        self.assertEqual(result[self.child_element.pk], [group_element.parent_element_id])

    def test_with_kwarg_is_root_when_matches_is_complementary_module_and_in_it(self):
        group_type = EducationGroupTypeFactory(
            name=GroupType.COMPLEMENTARY_MODULE.name,
            category=education_group_categories.GROUP
        )
        hierarchy = self._build_hierarchy(self.current_academic_year, group_type, self.child_element)
        result = program_management.ddd.repositories.find_roots.find_roots(
            [self.child_element],
            additional_root_categories=[GroupType.COMPLEMENTARY_MODULE]
        )

        self.assertEqual(result[self.child_element.pk], [hierarchy['group_element_child'].parent_element_id])


class TestConvertParentIdsToInstances(TestCase):
    """Unit tests for _convert_parent_ids_to_instances()"""

    def test_ids_correctly_converted_to_instances(self):
        group_element_leaf = GroupElementYearChildLeafFactory()

        root_ids_by_object_id = program_management.ddd.repositories.find_roots.find_roots([
            group_element_leaf.child_element
        ])
        result = program_management.ddd.repositories.find_roots._convert_parent_ids_to_instances(root_ids_by_object_id)
        expected_result = {
            group_element_leaf.child_element_id: [group_element_leaf.parent_element]
        }
        self.assertDictEqual(result, expected_result)
        self.assertIsInstance(list(result.keys())[0], int)
        self.assertIsInstance(result[group_element_leaf.child_element_id][0], Element)

    def test_ordered_by_acronym(self):
        element_learning_unit_year = ElementLearningUnitYearFactory()
        group_element1 = GroupElementYearFactory(
            parent_element__group_year__acronym='ECGE1BA',
            child_element=element_learning_unit_year
        )
        group_element2 = GroupElementYearFactory(
            parent_element__group_year__acronym='DROI1BA',
            child_element=element_learning_unit_year
        )
        group_element3 = GroupElementYearFactory(
            parent_element__group_year__acronym='SPOL2MS/G',
            child_element=element_learning_unit_year
        )
        root_ids_by_object_id = program_management.ddd.repositories.find_roots.find_roots([element_learning_unit_year])
        result = program_management.ddd.repositories.find_roots._convert_parent_ids_to_instances(root_ids_by_object_id)

        expected_order = [
            group_element2.parent_element,
            group_element1.parent_element,
            group_element3.parent_element
        ]
        self.assertListEqual(result[element_learning_unit_year.pk], expected_order)


class TestAssertSameObjectsClass(TestCase):
    def test_case_unothorized_instance(self):
        with self.assertRaises(AttributeError):
            program_management.ddd.repositories.find_roots._assert_same_objects_class([AcademicYearFactory()])

    def test_case_different_objects_instances(self):
        with self.assertRaises(AttributeError):
            program_management.ddd.repositories.find_roots._assert_same_objects_class(
                [EducationGroupYearFactory(), LearningUnitYearFactory()])

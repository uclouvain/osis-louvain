##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import random
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from base.models import group_element_year
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories, education_group_types
from base.models.enums.education_group_types import GroupType, MiniTrainingType, TrainingType
from base.models.enums.link_type import LinkTypes
from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, GroupFactory, MiniTrainingFactory, \
    TrainingFactory, EducationGroupYearMasterFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


class TestFindBuildParentListByEducationGroupYearId(TestCase):
    """Unit tests for _build_parent_list_by_education_group_year_id() function"""
    @classmethod
    def setUpTestData(cls):
        current_academic_year = create_current_academic_year()
        cls.root = TrainingFactory(
            academic_year=current_academic_year,
            education_group_type__name=TrainingType.BACHELOR.name
        )

        cls.child_branch = GroupFactory(academic_year=current_academic_year)
        GroupElementYearFactory(parent=cls.root, child_branch=cls.child_branch)

        cls.child_leaf = LearningUnitYearFactory(academic_year=current_academic_year)
        GroupElementYearFactory(parent=cls.child_branch, child_branch=None, child_leaf=cls.child_leaf)

    def test_with_filters(self):
        result = group_element_year._build_parent_list_by_education_group_year_id(self.child_leaf.academic_year)

        expected_result = {
            'base_educationgroupyear_{}'.format(self.child_branch.id): [{
                'parent': self.root.id,
                'child_branch': self.child_branch.id,
                'child_leaf': None,
                'parent__education_group_type__category': self.root.education_group_type.category,
                'parent__education_group_type__name': self.root.education_group_type.name,
            }, ],
            'base_learningunityear_{}'.format(self.child_leaf.id): [{
                'parent': self.child_branch.id,
                'child_branch': None,
                'child_leaf': self.child_leaf.id,
                'parent__education_group_type__category': self.child_branch.education_group_type.category,
                'parent__education_group_type__name': self.child_branch.education_group_type.name,
            }, ]
        }
        self.assertEqual(len(result), len(expected_result))
        self.assertDictEqual(result, expected_result)


class TestFindRelatedRootEducationGroups(TestCase):
    """Unit tests for find_learning_unit_roots() function"""

    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.child_leaf = LearningUnitYearFactory(academic_year=cls.current_academic_year)

        cls.root = TrainingFactory(
            academic_year=cls.current_academic_year,
            education_group_type__name=TrainingType.BACHELOR.name
        )

    @mock.patch('base.models.group_element_year._raise_if_incorrect_instance')
    def test_objects_instances_check_is_called(self, mock_check_instance):
        group_element_year.find_learning_unit_roots([self.child_leaf])
        self.assertTrue(mock_check_instance.called)

    def test_case_filters_arg_is_none(self):
        result = group_element_year.find_learning_unit_roots([self.child_leaf])
        expected_result = {
            self.child_leaf.id: []
        }
        self.assertDictEqual(result, expected_result)

    def test_with_filters_case_direct_parent_id_root_and_matches_filters(self):
        element_year = GroupElementYearFactory(parent=self.root, child_branch=None, child_leaf=self.child_leaf)
        result = group_element_year.find_learning_unit_roots([self.child_leaf])
        expected_result = {
            self.child_leaf.id: [element_year.parent.id]
        }

        self.assertEqual(result, expected_result)

    def test_with_filters_case_childs_with_different_academic_years(self):
        child_leaf_other_ac_year = LearningUnitYearFactory(
            academic_year=AcademicYearFactory(year=self.current_academic_year.year - 1)
        )
        with self.assertRaises(AttributeError):
            group_element_year.find_learning_unit_roots([self.child_leaf, child_leaf_other_ac_year])

    def test_with_filters_case_direct_parent_is_root_and_not_matches_filter(self):
        root = GroupFactory(
            academic_year=self.current_academic_year,
            education_group_type__name=GroupType.OPTION_LIST_CHOICE.name
        )
        GroupElementYearFactory(parent=root, child_branch=None, child_leaf=self.child_leaf)
        expected_result = {
            self.child_leaf.id: []
        }
        result = group_element_year.find_learning_unit_roots([self.child_leaf])
        self.assertDictEqual(result, expected_result)

    def test_with_filters_case_root_in_2nd_level_and_direct_parent_matches_filter(self):
        root = EducationGroupYearMasterFactory(academic_year=self.current_academic_year)
        child_branch = TrainingFactory(
            academic_year=self.current_academic_year,
            education_group_type__name=TrainingType.MASTER_MD_120.name
        )
        GroupElementYearFactory(parent=root, child_branch=child_branch)
        GroupElementYearFactory(parent=child_branch, child_branch=None, child_leaf=self.child_leaf)
        result = group_element_year.find_learning_unit_roots([self.child_leaf])
        expected_result = {
            self.child_leaf.id: [child_branch.id]
        }
        self.assertDictEqual(result, expected_result)
        self.assertNotIn(root.id, result)

    def test_with_filters_case_multiple_parents_in_2nd_level(self):
        root_2 = EducationGroupYearMasterFactory(academic_year=self.current_academic_year)
        child_branch = GroupFactory(academic_year=self.current_academic_year)

        GroupElementYearFactory(parent=self.root, child_branch=child_branch)
        GroupElementYearFactory(parent=root_2, child_branch=child_branch)
        GroupElementYearFactory(parent=child_branch, child_branch=None, child_leaf=self.child_leaf)
        result = group_element_year.find_learning_unit_roots([self.child_leaf])
        self.assertEqual(len(result[self.child_leaf.id]), 2)
        self.assertIn(self.root.id, result[self.child_leaf.id])
        self.assertIn(root_2.id, result[self.child_leaf.id])

    def test_with_filters_case_objects_are_education_group_instance(self):
        root = EducationGroupYearFactory(academic_year=self.current_academic_year)
        child_branch = EducationGroupYearFactory(academic_year=self.current_academic_year)
        GroupElementYearFactory(parent=root, child_branch=child_branch)
        result = group_element_year.find_learning_unit_roots([child_branch])
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
        result = group_element_year.find_learning_unit_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])

    def test_all_group_types_of_category_mini_training_stops_recursivity(self):
        group_type = EducationGroupTypeFactory(category=education_group_categories.MINI_TRAINING)
        hierarchy = self._build_hierarchy(self.current_academic_year, group_type, self.child_leaf)
        result = group_element_year.find_learning_unit_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])

    def test_all_group_types_of_category_training_stops_recursivity(self):
        type_bachelor = EducationGroupTypeFactory(
            name=TrainingType.BACHELOR.name, category=education_group_categories.TRAINING
        )
        hierarchy = self._build_hierarchy(self.current_academic_year, type_bachelor, self.child_leaf)
        result = group_element_year.find_learning_unit_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])

    def test_case_group_category_is_not_root(self):
        a_group_type = EducationGroupTypeFactory(name='Subgroup', category=education_group_categories.GROUP)
        hierarchy = self._build_hierarchy(self.current_academic_year, a_group_type, self.child_leaf)
        result = group_element_year.find_learning_unit_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])

    def test_case_group_category_is_root(self):
        a_group_type = EducationGroupTypeFactory(name='Subgroup', category=education_group_categories.GROUP)
        group_element = GroupElementYearFactory(
            parent=EducationGroupYearFactory(academic_year=self.current_academic_year,
                                             education_group_type=a_group_type),
            child_branch=None,
            child_leaf=self.child_leaf
        )
        result = group_element_year.find_learning_unit_roots([self.child_leaf])
        self.assertEqual(result[self.child_leaf.id], [])
        self.assertNotIn(group_element.parent.id, result[self.child_leaf.id])

    def test_case_arg_is_empty(self):
        result = group_element_year.find_learning_unit_roots([])
        self.assertEqual(result, {})

    def test_case_arg_is_none(self):
        result = group_element_year.find_learning_unit_roots(None)
        self.assertEqual(result, {})

    def test_with_kwarg_parents_as_instances_is_true(self):
        group_element = GroupElementYearFactory(
            child_branch=None,
            child_leaf=self.child_leaf
        )
        result = group_element_year.find_learning_unit_roots(
            [self.child_leaf],
            return_result_params={
                'parents_as_instances': True
            }
        )
        self.assertEqual(result[self.child_leaf.id], [group_element.parent])

    def test_with_kwarg_is_root_when_matches_is_complementary_module_and_not_in_it(self):
        group_element = GroupElementYearFactory(
            child_branch=None,
            child_leaf=self.child_leaf
        )
        result = group_element_year.find_learning_unit_roots(
            [self.child_leaf],
            luy=self.child_leaf,
            recursive_conditions={
                'stop': [GroupType.COMPLEMENTARY_MODULE.name],
                'continue': []
            }
        )
        self.assertEqual(result[self.child_leaf.id], [group_element.parent.id])

    def test_with_kwarg_is_root_when_matches_is_complementary_module_and_in_it(self):
        group_type = EducationGroupTypeFactory(
            name=GroupType.COMPLEMENTARY_MODULE.name,
            category=education_group_categories.GROUP
        )
        hierarchy = self._build_hierarchy(self.current_academic_year, group_type, self.child_leaf)
        result = group_element_year.find_learning_unit_roots(
            [self.child_leaf],
            luy=self.child_leaf,
            recursive_conditions={
                'stop': [GroupType.COMPLEMENTARY_MODULE.name],
                'continue': []
            }
        )

        self.assertEqual(result[self.child_leaf.id], [hierarchy['group_element_child'].parent.id])


class TestConvertParentIdsToInstances(TestCase):
    """Unit tests for _convert_parent_ids_to_instances()"""

    def test_ids_correctly_converted_to_instances(self):
        group_element = GroupElementYearFactory(
            child_branch=None,
            child_leaf=LearningUnitYearFactory()
        )
        root_ids_by_object_id = group_element_year.find_learning_unit_roots([group_element.child_leaf])
        result = group_element_year._convert_parent_ids_to_instances(root_ids_by_object_id)
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
        root_ids_by_object_id = group_element_year.find_learning_unit_roots([learn_unit_year])
        result = group_element_year._convert_parent_ids_to_instances(root_ids_by_object_id)
        expected_order = [group_element2.parent, group_element1.parent, group_element3.parent]
        self.assertListEqual(result[learn_unit_year.id], expected_order)

    def test_find_learning_unit_roots_improper_parameters(self):
        with self.assertRaisesMessage(
                ValueError,
                "If parameter with_parents_of_parents is True, parameter parents_as_instances must be True"):
            group_element_year.find_learning_unit_roots(
                [],
                return_result_params={
                    'parents_as_instances': False,
                    'with_parents_of_parents': True
                }
            )


class TestBuildChildKey(TestCase):
    """Unit tests on _build_child_key() """

    def test_case_params_are_none(self):
        with self.assertRaises(AttributeError):
            group_element_year._build_child_key()

    def test_case_two_params_are_set(self):
        with self.assertRaises(AttributeError):
            group_element_year._build_child_key(child_branch=1234, child_leaf=5678)

    def test_case_child_branch_is_set(self):
        result = group_element_year._build_child_key(child_branch=5678)
        self.assertEqual(result, 'base_educationgroupyear_5678')

    def test_case_child_leaf_is_set(self):
        result = group_element_year._build_child_key(child_leaf=5678)
        self.assertEqual(result, 'base_learningunityear_5678')


class TestRaiseIfIncorrectInstance(TestCase):
    def test_case_unothorized_instance(self):
        with self.assertRaises(AttributeError):
            group_element_year._raise_if_incorrect_instance([AcademicYearFactory()])

    def test_case_different_objects_instances(self):
        with self.assertRaises(AttributeError):
            group_element_year._raise_if_incorrect_instance(
                [EducationGroupYearFactory(), LearningUnitYearFactory()])


class TestManager(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_unit_year_1 = LearningUnitYearFactory()

        cls.learning_unit_year_without_container = LearningUnitYearFactory(
            learning_container_year=None
        )

        cls.group_element_year_1 = GroupElementYearFactory(
            child_branch=None,
            child_leaf=cls.learning_unit_year_1
        )

        cls.group_element_year_without_container = GroupElementYearFactory(
            child_branch=None,
            child_leaf=cls.learning_unit_year_without_container
        )

    def test_objects_without_container(self):
        self.assertNotIn(self.group_element_year_without_container, GroupElementYear.objects.all())
        self.assertIn(self.group_element_year_1, GroupElementYear.objects.all())


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

    def test_loop_save_on_itself_ko(self):
        egy = EducationGroupYearFactory()
        with self.assertRaises(ValidationError):
            GroupElementYearFactory(
                parent=egy,
                child_branch=egy,
            )

    def test_loop_save_ko(self):
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

        with self.assertRaises(ValidationError):
            GroupElementYearFactory(
                parent=egy1,
                child_branch=egy3,
            )

    def test_save_with_child_branch_and_child_leaf_ko(self):
        egy = EducationGroupYearFactory(academic_year=self.academic_year)
        luy = LearningUnitYearFactory()
        with self.assertRaises(ValidationError):
            GroupElementYearFactory(
                parent=egy,
                child_branch=egy,
                child_leaf=luy,
            )


class TestFetchGroupElementsBehindHierarchy(TestCase):
    """Unit tests on fetch_all_group_elements_behind_hierarchy()"""
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.root = EducationGroupYearMasterFactory(
            acronym='DROI2M',
            academic_year=cls.academic_year
        )

        finality_list = GroupFactory(
            acronym='LIST FINALITIES',
            education_group_type__name=education_group_types.GroupType.FINALITY_120_LIST_CHOICE.name,
            academic_year=cls.academic_year
        )

        formation_master_md = TrainingFactory(
            acronym='DROI2MD',
            education_group_type__name=education_group_types.TrainingType.MASTER_MD_120,
            academic_year=cls.academic_year
        )

        common_core = GroupFactory(
            acronym='TC DROI2MD',
            education_group_type__name=education_group_types.GroupType.COMMON_CORE,
            academic_year=cls.academic_year
        )

        cls.link_1 = GroupElementYearFactory(parent=cls.root, child_branch=finality_list, child_leaf=None)
        cls.link_1_bis = GroupElementYearFactory(parent=cls.root,
                                                 child_branch=EducationGroupYearFactory(
                                                     academic_year=cls.academic_year),
                                                 child_leaf=None)
        cls.link_2 = GroupElementYearFactory(parent=finality_list, child_branch=formation_master_md, child_leaf=None)
        cls.link_3 = GroupElementYearFactory(parent=formation_master_md, child_branch=common_core, child_leaf=None)
        cls.link_4 = GroupElementYearFactory(parent=common_core,
                                             child_leaf=LearningUnitYearFactory(),
                                             child_branch=None)

    def test_with_one_root_id(self):
        queryset = GroupElementYear.objects.all().select_related(
            'child_branch__academic_year',
            'child_leaf__academic_year',
            # [...] other fetch
        )
        result = group_element_year.fetch_all_group_elements_in_tree(self.root, queryset)
        expected_result = {
            self.link_1.parent_id: [self.link_1, self.link_1_bis],
            self.link_2.parent_id: [self.link_2],
            self.link_3.parent_id: [self.link_3],
            self.link_4.parent_id: [self.link_4],
        }
        self.assertDictEqual(result, expected_result)

    def test_when_queryset_is_not_from_group_element_year_model(self):
        wrong_queryset_model = EducationGroupYear.objects.all()
        with self.assertRaises(AttributeError):
            group_element_year.fetch_all_group_elements_in_tree(self.root, wrong_queryset_model)


class TestValidationOnEducationGroupYearBlockField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()

    def setUp(self):
        self.group_element_year = GroupElementYearFactory(parent__academic_year=self.academic_year,
                                                          child_branch__academic_year=self.academic_year)

    def test_when_value_is_higher_than_max_authorized(self):
        self.group_element_year.block = 7
        with self.assertRaises(ValidationError):
            self.group_element_year.full_clean()

    def test_when_more_than_6_digits_are_submitted(self):
        self.group_element_year.block = 1234567
        with self.assertRaises(ValidationError):
            self.group_element_year.full_clean()

    def test_when_values_are_duplicated(self):
        self.group_element_year.block = 1446
        with self.assertRaises(ValidationError):
            self.group_element_year.full_clean()

    def test_when_values_are_not_ordered(self):
        self.group_element_year.block = 54
        with self.assertRaises(ValidationError):
            self.group_element_year.full_clean()

    def test_when_0(self):
        self.group_element_year.block = 0
        with self.assertRaises(ValidationError):
            self.group_element_year.full_clean()

    def test_when_value_is_negative(self):
        self.group_element_year.block = -124
        with self.assertRaises(ValidationError):
            self.group_element_year.full_clean()

    def test_when_academic_year_diff_of_2_education_group(self):
        egy1 = EducationGroupYearFactory(academic_year=self.academic_year)
        egy2 = EducationGroupYearFactory(academic_year__year=self.academic_year.year + 1)
        with self.assertRaises(ValidationError):
            GroupElementYearFactory(
                parent=egy1,
                child_branch=egy2,
                child_leaf=None,
            )


class TestLinkTypeGroupElementYear(TestCase):
    def test_when_link_minor_to_minor_list_choice(self):
        minor_list_choice = GroupFactory(education_group_type__name=GroupType.MINOR_LIST_CHOICE.name)
        minor = MiniTrainingFactory(education_group_type__name=random.choice(MiniTrainingType.minors()))

        link = GroupElementYear(parent=minor_list_choice, child_branch=minor, link_type=None)
        link._clean_link_type()
        self.assertEqual(link.link_type, LinkTypes.REFERENCE.name)

    def test_when_link_deepening_to_minor_list_choice(self):
        minor_list_choice = GroupFactory(education_group_type__name=GroupType.MINOR_LIST_CHOICE.name)
        deepening = MiniTrainingFactory(education_group_type__name=MiniTrainingType.DEEPENING.name)

        link = GroupElementYear(parent=minor_list_choice, child_branch=deepening, link_type=None)
        link._clean_link_type()
        self.assertEqual(link.link_type, LinkTypes.REFERENCE.name)

    def test_when_link_major_to_major_list_choice(self):
        major_list_choice = GroupFactory(education_group_type__name=GroupType.MAJOR_LIST_CHOICE.name)
        major = MiniTrainingFactory(education_group_type__name=MiniTrainingType.FSA_SPECIALITY.name)

        link = GroupElementYear(parent=major_list_choice, child_branch=major, link_type=None)
        link._clean_link_type()
        self.assertEqual(link.link_type, LinkTypes.REFERENCE.name)


class TestManagerGetAdjacencyList(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_element_a = EducationGroupYearFactory()
        cls.level_1 = GroupElementYearFactory(parent=cls.root_element_a, order=0)
        cls.level_11 = GroupElementYearFactory(parent=cls.level_1.child_branch, order=0)
        cls.level_2 = GroupElementYearFactory(parent=cls.root_element_a, order=1)

        cls.root_element_b = EducationGroupYearFactory()
        GroupElementYearFactory(parent=cls.root_element_b, order=0)

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
            'child_branch_id':  self.level_1.child_branch_id,
            'child_leaf_id': None,
            'parent_id': self.level_1.parent_id,
            'child_id': self.level_1.child_branch_id,
            'order': 0,
            'level': 0,
            'path': "|".join([str(self.level_1.parent_id), str(self.level_1.child_branch_id)])
        }
        self.assertDictEqual(adjacency_list[0], expected_first_elem)

    def test_case_multiple_root_elements_ids(self):
        adjacency_list = GroupElementYear.objects.get_adjacency_list([self.root_element_a.pk, self.root_element_b.pk])
        self.assertEqual(len(adjacency_list), 4)


class TestManagerGetReverseAdjacencyList(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_element_a = EducationGroupYearFactory()
        cls.level_1 = GroupElementYearFactory(parent=cls.root_element_a)
        cls.level_11 = GroupElementYearFactory(parent=cls.level_1.child_branch)
        cls.level_111 = GroupElementYearFactory(
            parent=cls.level_11.child_branch,
            child_branch=None,
            child_leaf=LearningUnitYearFactory(),
        )
        cls.level_2 = GroupElementYearFactory(
            parent=cls.root_element_a,
            child_branch=None,
            child_leaf=LearningUnitYearFactory(),
            order=5
        )

    def test_case_root_elements_ids_args_is_not_a_correct_instance(self):
        with self.assertRaises(Exception):
            GroupElementYear.objects.get_reverse_adjacency_list(child_leaf_ids='bad_args')

    def test_case_root_elements_ids_is_empty(self):
        reverse_adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(child_leaf_ids=[])
        self.assertEqual(len(reverse_adjacency_list), 0)

    def test_case_filter_by_child_ids(self):
        reverse_adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(
            child_leaf_ids=[self.level_2.child_leaf_id]
        )
        self.assertEqual(len(reverse_adjacency_list), 1)

        expected_first_elem = {
            'starting_node_id': self.level_2.child_leaf_id,
            'id': self.level_2.pk,
            'child_branch_id': None,
            'child_leaf_id': self.level_2.child_leaf_id,
            'parent_id': self.level_2.parent_id,
            'child_id': self.level_2.child_leaf_id,
            'order': self.level_2.order,
            'level': 0,
        }
        self.assertDictEqual(reverse_adjacency_list[0], expected_first_elem)

    def test_case_multiple_child_ids(self):
        adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(child_leaf_ids=[
            self.level_2.child_leaf_id,
            self.level_111.child_leaf_id
        ])
        self.assertEqual(len(adjacency_list), 4)

    def test_case_child_is_education_group_instance(self):
        level_2bis = GroupElementYearFactory(
            parent=self.root_element_a,
            order=6
        )
        reverse_adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(
            child_branch_ids=[level_2bis.child_branch.id]
        )
        self.assertEqual(len(reverse_adjacency_list), 1)

    def test_case_child_leaf_and_child_branch_have_same_id(self):
        common_id = 123456
        # with parent
        link_with_leaf = GroupElementYearFactory(
            child_branch=None,
            child_leaf=LearningUnitYearFactory(id=common_id),
            parent=self.root_element_a,
        )
        # Without parent
        link_with_branch = GroupElementYearFactory(
            child_branch__id=common_id,
        )
        reverse_adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(
            child_branch_ids=[link_with_leaf.child_leaf.id, link_with_branch.child_branch.id]
        )
        self.assertEqual(len(reverse_adjacency_list), 1)
        self.assertNotEqual(len(reverse_adjacency_list), 2)

    def test_case_filter_link_type(self):
        link_reference = GroupElementYearFactory(
            parent__academic_year=self.level_1.child_branch.academic_year,
            child_branch=self.level_1.child_branch,
            order=6,
            link_type=LinkTypes.REFERENCE.name
        )
        link_not_reference = GroupElementYearFactory(
            parent__academic_year=self.level_1.child_branch.academic_year,
            child_branch=self.level_1.child_branch,
            order=6,
            link_type=None
        )
        reverse_adjacency_list = GroupElementYear.objects.get_reverse_adjacency_list(
            child_branch_ids=[self.level_1.child_branch.id],
            link_type=LinkTypes.REFERENCE,
        )
        result_parent_ids = [rec['parent_id'] for rec in reverse_adjacency_list]
        self.assertIn(link_reference.parent.id, result_parent_ids)
        self.assertNotIn(link_not_reference.parent.id, result_parent_ids)

##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.conf import settings
from django.test import TestCase, RequestFactory
from rest_framework.reverse import reverse

from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from base.models.enums.link_type import LinkTypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory, GroupFactory, MiniTrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory
from education_group.api.serializers.group_element_year import EducationGroupRootNodeTreeSerializer
from education_group.api.views.group import GroupDetail
from education_group.api.views.group_element_year import TrainingTreeView, GroupTreeView
from education_group.api.views.training import TrainingDetail
from education_group.enums.node_type import NodeType
from learning_unit.api.views.learning_unit import LearningUnitDetailed
from program_management.ddd.domain.link import Link
from program_management.ddd.repositories import load_tree


class EducationGroupRootNodeTreeSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        BIR1BA
        |--Common Core
           |-- Learning unit year
        """
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.training = TrainingFactory(
            acronym='BIR1BA',
            partial_acronym='LBIR100B',
            academic_year=cls.academic_year,
            education_group_type__name=TrainingType.BACHELOR.name
        )
        cls.common_core = GroupFactory(
            education_group_type__name=GroupType.COMMON_CORE.name,
            academic_year=cls.academic_year
        )
        cls.gey_no_child_leaf = GroupElementYearFactory(
            parent=cls.training, child_branch=cls.common_core, child_leaf=None
        )

        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year,
            credits=10,
            status=False,
            specific_title_english=None,
            learning_container_year__common_title_english='COMMON'
        )
        cls.luy_gey = GroupElementYearFactory(
            parent=cls.common_core, child_branch=None, child_leaf=cls.learning_unit_year, relative_credits=15
        )

        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs={
            'acronym': cls.training.acronym,
            'year': cls.academic_year.year
        })
        cls.serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(cls.training.id).root_node),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )

    def test_root_contains_expected_fields(self):
        expected_fields = [
            'url',
            'title',
            'children',
            'node_type',
            'subtype',
            'acronym',
            'code',
            'remark',
            'min_constraint',
            'max_constraint',
            'constraint_type'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_children_contains_expected_fields(self):
        expected_fields = [
            'url',
            'title',
            'children',
            'is_mandatory',
            'access_condition',
            'comment',
            'link_type',
            'link_type_text',
            'block',
            'credits',
            'node_type',
            'subtype',
            'acronym',
            'code',
            'remark',
            'min_constraint',
            'max_constraint',
            'constraint_type'
        ]
        self.assertListEqual(list(self.serializer.data['children'][0].keys()), expected_fields)

    def test_learning_unit_children_contains_expected_fields(self):
        expected_fields = [
            'url',
            'title',
            'is_mandatory',
            'access_condition',
            'comment',
            'link_type',
            'link_type_text',
            'block',
            'credits',
            'node_type',
            'subtype',
            'code',
            'remark',
            'lecturing_volume',
            'practical_exercise_volume',
            'with_prerequisite',
            'periodicity',
            'quadrimester',
            'status',
            'proposal_type'
        ]
        self.assertListEqual(list(self.serializer.data['children'][0]['children'][0].keys()), expected_fields)

    def test_learning_unit_children_have_only_common_title_if_no_specific_one(self):
        luy = self.serializer.data['children'][0]['children'][0]
        self.assertEqual(luy['title'], 'COMMON')

    def test_learning_unit_children_status_field_is_false_boolean(self):
        luy = self.serializer.data['children'][0]['children'][0]
        self.assertFalse(luy['status'])

    def test_ensure_not_getting_direct_child_of_reference_link(self):
        training = TrainingFactory(
            academic_year=self.academic_year,
            education_group_type__name=TrainingType.BACHELOR.name
        )
        common_core = GroupFactory(
            education_group_type__name=GroupType.COMMON_CORE.name,
            academic_year=self.academic_year
        )
        GroupElementYearFactory(
            parent=training, child_branch=common_core, child_leaf=None, link_type=LinkTypes.REFERENCE.name
        )
        luy = LearningUnitYearFactory(academic_year=self.academic_year)
        GroupElementYearFactory(parent=common_core, child_branch=None, child_leaf=luy)
        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs={
            'acronym': training.acronym,
            'year': self.academic_year.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(training.id).root_node),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        self.assertEqual(len(serializer.data['children']), 1)
        self.assertEqual(serializer.data['children'][0]['code'], luy.acronym)

    def test_ensure_not_getting_direct_child_of_reference_link_except_within_minor_list(self):
        training = TrainingFactory(
            academic_year=self.academic_year,
            education_group_type__name=GroupType.MINOR_LIST_CHOICE.name
        )
        minor = MiniTrainingFactory(
            education_group_type__name=MiniTrainingType.ACCESS_MINOR.name,
            academic_year=self.academic_year
        )
        GroupElementYearFactory(
            parent=training, child_branch=minor, child_leaf=None, link_type=LinkTypes.REFERENCE.name
        )
        luy = LearningUnitYearFactory(academic_year=self.academic_year)
        GroupElementYearFactory(parent=minor, child_branch=None, child_leaf=luy)
        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs={
            'acronym': training.acronym,
            'year': self.academic_year.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(training.id).root_node),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        self.assertEqual(len(serializer.data['children']), 1)
        self.assertEqual(serializer.data['children'][0]['code'], minor.partial_acronym)

    def test_ensure_node_type_and_subtype_expected(self):
        self.assertEqual(self.serializer.data['node_type'], NodeType.TRAINING.name)
        self.assertEqual(self.serializer.data['subtype'], self.training.education_group_type.name)
        self.assertEqual(self.serializer.data['children'][0]['node_type'], NodeType.GROUP.name)
        self.assertEqual(self.serializer.data['children'][0]['subtype'], self.common_core.education_group_type.name)
        self.assertEqual(self.serializer.data['children'][0]['children'][0]['node_type'], NodeType.LEARNING_UNIT.name)
        self.assertEqual(
            self.serializer.data['children'][0]['children'][0]['subtype'],
            self.learning_unit_year.learning_container_year.container_type
        )

    def test_get_with_prerequisites(self):
        self.assertFalse(self.serializer.data['children'][0]['children'][0]['with_prerequisite'])

        luy = LearningUnitYearFactory(
            academic_year=self.academic_year,
            learning_container_year__academic_year=self.academic_year
        )
        gey = GroupElementYearFactory(
            parent__education_group_type__name=GroupType.COMMON_CORE.name,
            child_branch=None,
            child_leaf=luy,
            relative_credits=None
        )
        PrerequisiteItemFactory(
            prerequisite__learning_unit_year=luy,
            prerequisite__education_group_year=gey.parent
        )
        url = reverse('education_group_api_v1:' + GroupTreeView.name, kwargs={
            'partial_acronym': gey.parent.partial_acronym,
            'year': self.academic_year.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(gey.parent.id).root_node),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        self.assertTrue(serializer.data['children'][0]['with_prerequisite'])

    def test_get_appropriate_credits_for_luy(self):
        self.assertEqual(self.serializer.data['children'][0]['children'][0]['credits'],
                         self.luy_gey.relative_credits or self.luy_gey.child_leaf.credits)

        luy = LearningUnitYearFactory(
            academic_year=self.academic_year,
            learning_container_year__academic_year=self.academic_year
        )
        gey = GroupElementYearFactory(
            parent__education_group_type__name=GroupType.COMMON_CORE.name,
            child_branch=None,
            child_leaf=luy,
            relative_credits=None
        )
        url = reverse('education_group_api_v1:' + GroupTreeView.name, kwargs={
            'partial_acronym': gey.parent.partial_acronym,
            'year': self.academic_year.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(gey.parent.id).root_node),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        self.assertEqual(serializer.data['children'][0]['credits'], luy.credits,
                         'should get absolute credits if no relative credits')

    def test_get_appropriate_credits_for_egy(self):
        egy = GroupFactory(
            academic_year=self.academic_year,
            education_group_type__name=GroupType.SUB_GROUP.name,
        )
        gey = GroupElementYearFactory(
            parent__education_group_type__name=GroupType.COMMON_CORE.name,
            parent__academic_year=self.academic_year,
            child_branch=egy,
            child_leaf=None,
            relative_credits=None
        )
        url = reverse('education_group_api_v1:' + GroupTreeView.name, kwargs={
            'partial_acronym': gey.parent.partial_acronym,
            'year': self.academic_year.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(gey.parent.id).root_node),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        self.assertEqual(serializer.data['children'][0]['credits'], egy.credits,
                         'should get absolute credits if no relative credits')

    def test_get_appropriate_relative_credits(self):
        expected_credits = 10
        serializer = self.expected_credits(15, expected_credits)
        self.assertEqual(serializer.data['children'][0]['credits'], expected_credits)

    def test_get_appropriate_absolute_credits(self):
        expected_credits = 15
        serializer = self.expected_credits(expected_credits, None)
        self.assertEqual(serializer.data['children'][0]['credits'], expected_credits)

    def test_ensure_url_is_related_to_instance(self):
        expected_root_url = reverse('education_group_api_v1:' + TrainingDetail.name, kwargs={
            'acronym': self.training.acronym,
            'year': self.training.academic_year.year,
        })
        self.assertIn(expected_root_url, self.serializer.data['url'])

        expected_group_url = reverse('education_group_api_v1:' + GroupDetail.name, kwargs={
            'partial_acronym': self.common_core.partial_acronym,
            'year': self.common_core.academic_year.year,
        })
        self.assertIn(expected_group_url, self.serializer.data['children'][0]['url'])

        expected_learning_unit_url = reverse('learning_unit_api_v1:' + LearningUnitDetailed.name, kwargs={
            'acronym': self.learning_unit_year.acronym,
            'year': self.learning_unit_year.academic_year.year,
        })
        self.assertIn(expected_learning_unit_url, self.serializer.data['children'][0]['children'][0]['url'])

    def test_ensure_title_is_related_to_instance_and_language_of_serializer(self):
        self.assertIn(self.serializer.data['title'], self.training.title_english)
        self.assertEqual(self.serializer.data['children'][0]['title'], self.common_core.title_english)
        self.assertEqual(
            self.serializer.data['children'][0]['children'][0]['title'],
            self.learning_unit_year.complete_title_english,
        )

    def expected_credits(self, absolute_credits, relative_credits):
        luy = LearningUnitYearFactory(
            academic_year=self.academic_year,
            learning_container_year__academic_year=self.academic_year,
            credits=absolute_credits
        )
        gey = GroupElementYearFactory(
            parent__education_group_type__name=GroupType.COMMON_CORE.name,
            child_branch=None,
            child_leaf=luy,
            relative_credits=relative_credits
        )
        url = reverse('education_group_api_v1:' + GroupTreeView.name, kwargs={
            'partial_acronym': gey.parent.partial_acronym,
            'year': self.academic_year.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(gey.parent.id).root_node),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        return serializer


class EducationGroupWithMasterFinalityInRootTreeSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        GERM2MA
        |--Common Core
           |-- Learning unit year
        """
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.training = TrainingFactory(
            acronym='GERM2MA',
            partial_acronym='LGERM905A',
            academic_year=cls.academic_year,
            education_group_type__name=TrainingType.MASTER_MA_120.name,
        )
        cls.common_core = GroupFactory(
            education_group_type__name=GroupType.COMMON_CORE.name,
            academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.training, child_branch=cls.common_core, child_leaf=None)

        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.common_core, child_branch=None, child_leaf=cls.learning_unit_year)

        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs={
            'acronym': cls.training.acronym,
            'year': cls.academic_year.year
        })
        cls.serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(cls.training.id).root_node),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )

    def test_root_contains_expected_fields(self):
        expected_fields = [
            'url',
            'title',
            'children',
            'node_type',
            'subtype',
            'acronym',
            'code',
            'remark',
            'partial_title',
            'min_constraint',
            'max_constraint',
            'constraint_type'
        ]
        self.assertListEqual(expected_fields, list(self.serializer.data.keys()))

    def test_children_contains_expected_fields(self):
        expected_fields = [
            'url',
            'title',
            'children',
            'is_mandatory',
            'access_condition',
            'comment',
            'link_type',
            'link_type_text',
            'block',
            'credits',
            'node_type',
            'subtype',
            'acronym',
            'code',
            'remark',
            'min_constraint',
            'max_constraint',
            'constraint_type'
        ]
        self.assertListEqual(expected_fields, list(self.serializer.data['children'][0].keys()))


class EducationGroupWithMasterFinalityInChildTreeSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        GERM2M
        |--Common Core
           |-- GERM2MA
              |-- Learning unit year
        """
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.training = TrainingFactory(
            acronym='GERM2M',
            partial_acronym='LGERM905',
            academic_year=cls.academic_year,
            education_group_type__name=TrainingType.PGRM_MASTER_120.name,
        )
        cls.training_2 = TrainingFactory(
            acronym='GERM2MA',
            partial_acronym='LGERM905A',
            academic_year=cls.academic_year,
            education_group_type__name=TrainingType.MASTER_MA_120.name,
        )
        cls.common_core = GroupFactory(
            education_group_type__name=GroupType.COMMON_CORE.name,
            academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.training, child_branch=cls.common_core, child_leaf=None)
        GroupElementYearFactory(parent=cls.common_core, child_branch=cls.training_2, child_leaf=None)
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.training_2, child_branch=None, child_leaf=cls.learning_unit_year)

        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs={
            'acronym': cls.training.acronym,
            'year': cls.academic_year.year
        })
        cls.serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(cls.training.id).root_node),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )

    def test_root_contains_expected_fields(self):
        expected_fields = [
            'url',
            'title',
            'children',
            'node_type',
            'subtype',
            'acronym',
            'code',
            'remark',
            'min_constraint',
            'max_constraint',
            'constraint_type'
        ]
        self.assertListEqual(expected_fields, list(self.serializer.data.keys()))

    def test_children_contains_expected_fields(self):
        expected_fields = [
            'url',
            'title',
            'children',
            'is_mandatory',
            'access_condition',
            'comment',
            'link_type',
            'link_type_text',
            'block',
            'credits',
            'node_type',
            'subtype',
            'acronym',
            'code',
            'remark',
            'partial_title',
            'min_constraint',
            'max_constraint',
            'constraint_type'
        ]
        self.assertListEqual(expected_fields, list(self.serializer.data['children'][0]['children'][0].keys()))

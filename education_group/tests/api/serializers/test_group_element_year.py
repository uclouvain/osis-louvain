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
from unittest import skip

from django.conf import settings
from django.test import RequestFactory, SimpleTestCase
from rest_framework.reverse import reverse

from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from base.models.enums.link_type import LinkTypes
from education_group.api.serializers.group_element_year import EducationGroupRootNodeTreeSerializer
from education_group.api.views.group import GroupDetail
from education_group.api.views.group_element_year import TrainingTreeView, GroupTreeView
from education_group.api.views.training import TrainingDetail
from education_group.enums.node_type import NodeType
from learning_unit.api.views.learning_unit import LearningUnitDetailed
from program_management.ddd.domain.link import Link
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.prerequisite import PrerequisiteFactory


class EducationGroupRootNodeTreeSerializerTestCase(SimpleTestCase):
    def setUp(self) -> None:
        """
        BIR1BA
        |--Common Core
           |-- Learning unit year
        """
        self.year = 2018
        self.training = NodeGroupYearFactory(
            title='BIR1BA',
            code='LBIR100B',
            year=self.year,
            node_type=TrainingType.BACHELOR
        )
        self.common_core = NodeGroupYearFactory(
            node_type=GroupType.COMMON_CORE,
            year=self.year
        )
        self.gey_no_child_leaf = LinkFactory(
            parent=self.training, child=self.common_core
        )

        self.learning_unit_year = NodeLearningUnitYearFactory(
            year=self.year,
            credits=10,
            status=False,
            specific_title_en=None,
            common_title_en='COMMON'
        )
        self.luy_gey = LinkFactory(
            parent=self.common_core, child=self.learning_unit_year, relative_credits=15
        )

        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs={
            'acronym': self.training.title,
            'year': self.year
        })
        self.serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=self.training),
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
        keys = self.serializer.data['children'][0].keys()
        diff = set(keys).symmetric_difference(expected_fields)
        self.assertListEqual(list(keys), expected_fields, str(diff))

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

    @skip("FIXME in OSIS-4561")
    def test_ensure_not_getting_direct_child_of_reference_link(self):
        training = NodeGroupYearFactory(
            year=self.year,
            node_type=TrainingType.BACHELOR
        )
        common_core = NodeGroupYearFactory(
            year=self.year,
            node_type=GroupType.COMMON_CORE,
        )
        LinkFactory(
            parent=training, child=common_core, link_type=LinkTypes.REFERENCE
        )
        luy = NodeLearningUnitYearFactory(year=self.year)
        LinkFactory(parent=common_core, child=luy)
        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs={
            'acronym': training.title,
            'year': self.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=self.training),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        self.assertEqual(len(serializer.data['children']), 1)
        self.assertEqual(serializer.data['children'][0]['children'][0]['code'], luy.code)

    def test_ensure_not_getting_direct_child_of_reference_link_except_within_minor_list(self):
        training = NodeGroupYearFactory(
            year=self.year,
            node_type=GroupType.MINOR_LIST_CHOICE
        )
        minor = NodeGroupYearFactory(
            year=self.year,
            node_type=MiniTrainingType.ACCESS_MINOR,
        )
        LinkFactory(
            parent=training, child=minor, link_type=LinkTypes.REFERENCE
        )
        luy = NodeLearningUnitYearFactory(year=self.year)
        LinkFactory(parent=minor, child=luy)
        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs={
            'acronym': training.title,
            'year': self.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=training),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        self.assertEqual(len(serializer.data['children']), 1)
        self.assertEqual(serializer.data['children'][0]['code'], minor.code)

    def test_ensure_node_type_and_subtype_expected(self):
        self.assertEqual(self.serializer.data['node_type'], NodeType.TRAINING.name)
        self.assertEqual(self.serializer.data['subtype'], self.training.node_type.name)
        self.assertEqual(self.serializer.data['children'][0]['node_type'], NodeType.GROUP.name)
        self.assertEqual(self.serializer.data['children'][0]['subtype'], self.common_core.node_type.name)
        self.assertEqual(self.serializer.data['children'][0]['children'][0]['node_type'], NodeType.LEARNING_UNIT.name)
        self.assertEqual(
            self.serializer.data['children'][0]['children'][0]['subtype'],
            self.learning_unit_year.learning_unit_type.name
        )

    def test_get_with_prerequisites(self):
        self.assertFalse(self.serializer.data['children'][0]['children'][0]['with_prerequisite'])

        luy = NodeLearningUnitYearFactory(
            year=self.year,
        )
        luy.set_prerequisite(PrerequisiteFactory())
        gey = LinkFactory(
            parent__node_type=GroupType.COMMON_CORE,
            child=luy,
            relative_credits=None
        )
        url = reverse('education_group_api_v1:' + GroupTreeView.name, kwargs={
            'partial_acronym': gey.parent.code,
            'year': self.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=gey.parent),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        self.assertTrue(serializer.data['children'][0]['with_prerequisite'])

    def test_get_appropriate_credits_for_luy(self):
        self.assertEqual(self.serializer.data['children'][0]['children'][0]['credits'],
                         self.luy_gey.relative_credits or self.luy_gey.child_leaf.credits)

        luy = NodeLearningUnitYearFactory(year=self.year)
        gey = LinkFactory(
            parent__node_type=GroupType.COMMON_CORE,
            child=luy,
            relative_credits=None
        )
        url = reverse('education_group_api_v1:' + GroupTreeView.name, kwargs={
            'partial_acronym': gey.parent.code,
            'year': self.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=gey.parent),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        self.assertEqual(serializer.data['children'][0]['credits'], luy.credits,
                         'should get absolute credits if no relative credits')

    def test_get_appropriate_credits_for_egy(self):
        egy = NodeGroupYearFactory(
            year=self.year,
            node_type=GroupType.SUB_GROUP
        )
        gey = LinkFactory(
            parent__node_type=GroupType.COMMON_CORE,
            parent__year=self.year,
            child=egy,
            relative_credits=None
        )
        url = reverse('education_group_api_v1:' + GroupTreeView.name, kwargs={
            'partial_acronym': gey.parent.code,
            'year': self.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=gey.parent),
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
            'acronym': self.training.title,
            'year': self.training.year,
        })
        self.assertIn(expected_root_url, self.serializer.data['url'])

        expected_group_url = reverse('education_group_api_v1:' + GroupDetail.name, kwargs={
            'partial_acronym': self.common_core.code,
            'year': self.common_core.year,
        })
        self.assertIn(expected_group_url, self.serializer.data['children'][0]['url'])

        expected_learning_unit_url = reverse('learning_unit_api_v1:' + LearningUnitDetailed.name, kwargs={
            'acronym': self.learning_unit_year.code,
            'year': self.learning_unit_year.year,
        })
        self.assertIn(expected_learning_unit_url, self.serializer.data['children'][0]['children'][0]['url'])

    def test_ensure_title_is_related_to_instance_and_language_of_serializer(self):
        self.assertIn(self.serializer.data['title'], self.training.offer_title_en)
        self.assertEqual(self.serializer.data['children'][0]['title'], self.common_core.group_title_en)
        self.assertEqual(
            self.serializer.data['children'][0]['children'][0]['title'],
            self.learning_unit_year.common_title_en + (self.learning_unit_year.specific_title_en or ''),
        )

    def expected_credits(self, absolute_credits, relative_credits):
        luy = NodeLearningUnitYearFactory(
            year=self.year,
            credits=absolute_credits
        )
        gey = LinkFactory(
            parent__node_type=GroupType.COMMON_CORE,
            child=luy,
            relative_credits=relative_credits
        )
        url = reverse('education_group_api_v1:' + GroupTreeView.name, kwargs={
            'partial_acronym': gey.parent.code,
            'year': self.year
        })
        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=gey.parent),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )
        return serializer


class EducationGroupWithMasterFinalityInRootTreeSerializerTestCase(SimpleTestCase):

    def setUp(self) -> None:
        """
        GERM2MA
        |--Common Core
           |-- Learning unit year
        """
        self.year = 2018
        self.training = NodeGroupYearFactory(
            title='GERM2MA',
            code='LGERM905A',
            year=self.year,
            node_type=TrainingType.MASTER_MA_120,
        )
        self.common_core = NodeGroupYearFactory(
            node_type=GroupType.COMMON_CORE,
            year=self.year
        )
        LinkFactory(parent=self.training, child=self.common_core)

        self.learning_unit_year = NodeLearningUnitYearFactory(year=self.year)
        LinkFactory(parent=self.common_core, child=self.learning_unit_year)

        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs={
            'acronym': self.training.title,
            'year': self.year
        })
        self.serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=self.training),
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


class EducationGroupWithMasterFinalityInChildTreeSerializerTestCase(SimpleTestCase):

    def setUp(self) -> None:
        """
        GERM2M
        |--Common Core
           |-- GERM2MA
              |-- Learning unit year
        """
        self.year = 2018
        self.training = NodeGroupYearFactory(
            title='GERM2M',
            code='LGERM905',
            year=self.year,
            node_type=TrainingType.PGRM_MASTER_120,
        )
        self.training_2 = NodeGroupYearFactory(
            title='GERM2MA',
            code='LGERM905A',
            year=self.year,
            node_type=TrainingType.MASTER_MA_120,
        )
        self.common_core = NodeGroupYearFactory(
            node_type=GroupType.COMMON_CORE,
            year=self.year
        )
        LinkFactory(parent=self.training, child=self.common_core)
        LinkFactory(parent=self.common_core, child=self.training_2)
        self.learning_unit_year = NodeLearningUnitYearFactory(year=self.year)
        LinkFactory(parent=self.training_2, child=self.learning_unit_year)

        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs={
            'acronym': self.training.title,
            'year': self.year
        })
        self.serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=self.training),
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

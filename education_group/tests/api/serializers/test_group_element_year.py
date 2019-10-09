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

from base.business.education_groups.group_element_year_tree import EducationGroupHierarchy
from base.models.enums.education_group_types import TrainingType, GroupType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory, GroupFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from education_group.api.serializers.group_element_year import EducationGroupTreeSerializer
from education_group.api.views.group import GroupDetail
from education_group.api.views.group_element_year import TrainingTreeView
from education_group.api.views.training import TrainingDetail
from education_group.enums.node_type import NodeType
from learning_unit.api.views.learning_unit import LearningUnitDetailed


class EducationGroupTreeSerializerTestCase(TestCase):
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
        cls.serializer = EducationGroupTreeSerializer(
            EducationGroupHierarchy(cls.training),
            context={
                'request': RequestFactory().get(url),
                'language': settings.LANGUAGE_CODE_EN
            }
        )

    def test_root_contains_expected_fields(self):
        expected_fields = [
            'url',
            'acronym',
            'code',
            'title',
            'node_type',
            'children',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_children_contains_expected_fields(self):
        expected_fields = [
            'url',
            'acronym',
            'code',
            'title',
            'node_type',
            'relative_credits',
            'is_mandatory',
            'access_condition',
            'comment',
            'link_type',
            'link_type_text',
            'block',
            'children',
        ]
        self.assertListEqual(list(self.serializer.data['children'][0].keys()), expected_fields)

    def test_ensure_node_type_expected(self):
        self.assertEqual(self.serializer.data['node_type'], NodeType.TRAINING.name)
        self.assertEqual(self.serializer.data['children'][0]['node_type'], NodeType.GROUP.name)
        self.assertEqual(self.serializer.data['children'][0]['children'][0]['node_type'], NodeType.LEARNING_UNIT.name)

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

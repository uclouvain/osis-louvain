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
from django.test import TestCase, RequestFactory
from django.urls import reverse

from base.models.enums import organization_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory
from base.tests.factories.entity_version import EntityVersionFactory
from education_group.api.serializers.training import TrainingListSerializer, TrainingDetailSerializer


class TrainingListSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.entity_version = EntityVersionFactory(
            entity__organization__type=organization_type.MAIN
        )
        cls.training = TrainingFactory(
            acronym='BIR1BA',
            partial_acronym='LBIR1000I',
            academic_year=cls.academic_year,
            management_entity=cls.entity_version.entity,
            administration_entity=cls.entity_version.entity,
        )
        url = reverse('education_group_api_v1:training-list')
        cls.serializer = TrainingListSerializer(cls.training, context={'request': RequestFactory().get(url)})

    def test_contains_expected_fields(self):
        expected_fields = [
            'url',
            'acronym',
            'code',
            'education_group_type',
            'education_group_type_text',
            'title',
            'title_english',
            'academic_year',
            'administration_entity',
            'management_entity',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_ensure_academic_year_field_is_slugified(self):
        self.assertEqual(
            self.serializer.data['academic_year'],
            self.academic_year.year
        )

    def test_ensure_education_group_type_field_is_slugified(self):
        self.assertEqual(
            self.serializer.data['education_group_type'],
            self.training.education_group_type.name
        )


class TrainingDetailSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.entity_version = EntityVersionFactory(
            entity__organization__type=organization_type.MAIN
        )
        cls.training = TrainingFactory(
            acronym='BIR1BA',
            partial_acronym='LBIR1000I',
            academic_year=cls.academic_year,
            management_entity=cls.entity_version.entity,
            administration_entity=cls.entity_version.entity,
        )
        url = reverse('education_group_api_v1:training-detail', kwargs={'uuid': cls.training.uuid})
        cls.serializer = TrainingDetailSerializer(cls.training, context={'request': RequestFactory().get(url)})

    def test_contains_expected_fields(self):
        expected_fields = [
            'url',
            'acronym',
            'code',
            'education_group_type',
            'education_group_type_text',
            'title',
            'title_english',
            'academic_year',
            'administration_entity',
            'management_entity',
            'partial_deliberation',
            'admission_exam',
            'funding',
            'funding_direction',
            'funding_cud',
            'funding_direction_cud',
            'academic_type',
            'academic_type_text',
            'university_certificate',
            'dissertation',
            'internship',
            'internship_text',
            'schedule_type',
            'schedule_type_text',
            'english_activities',
            'english_activities_text',
            'other_language_activities',
            'other_language_activities_text',
            'other_campus_activities',
            'other_campus_activities_text',
            'professional_title',
            'joint_diploma',
            'diploma_printing_orientation',
            'diploma_printing_orientation_text',
            'diploma_printing_title',
            'inter_organization_information',
            'inter_university_french_community',
            'inter_university_belgium',
            'inter_university_abroad',
            'primary_language',
            'keywords',
            'duration',
            'duration_unit',
            'duration_unit_text',
            'enrollment_enabled',
            'credits',
            'remark',
            'remark_english',
            'min_constraint',
            'max_constraint',
            'constraint_type_text',
            'constraint_type',
            'weighting',
            'default_learning_unit_enrollment',
            'decree_category',
            'decree_category_text',
            'rate_code',
            'rate_code_text',
            'internal_comment',
            'co_graduation',
            'co_graduation_coefficient',
            'web_re_registration',
            'active',
            'active_text',
            'enrollment_campus',
            'main_teaching_campus',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_ensure_academic_year_field_is_slugified(self):
        self.assertEqual(
            self.serializer.data['academic_year'],
            self.academic_year.year
        )

    def test_ensure_education_group_type_field_is_slugified(self):
        self.assertEqual(
            self.serializer.data['education_group_type'],
            self.training.education_group_type.name
        )

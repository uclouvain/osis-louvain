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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.conf import settings
from django.test import TestCase

from base.models.enums.education_group_types import TrainingType
from base.tests.factories.admission_condition import AdmissionConditionFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, \
    EducationGroupYearCommonBachelorFactory, EducationGroupYearCommonSpecializedMasterFactory, \
    EducationGroupYearCommonAgregationFactory, EducationGroupYearCommonMasterFactory, TrainingFactory
from webservices.api.serializers.admission_condition import AdmissionConditionsSerializer, \
    BachelorAdmissionConditionsSerializer, SpecializedMasterAdmissionConditionsSerializer, \
    AggregationAdmissionConditionsSerializer, MasterAdmissionConditionsSerializer


class AdmissionConditionsSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        egy = EducationGroupYearFactory(education_group_type__name=TrainingType.CERTIFICATE.name)
        cls.ac = AdmissionConditionFactory(education_group_year=egy)
        cls.serializer = AdmissionConditionsSerializer(cls.ac, context={
            'lang': settings.LANGUAGE_CODE_EN,
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'free_text',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)


class BachelorAdmissionConditionsSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        egy = EducationGroupYearFactory(education_group_type__name=TrainingType.BACHELOR.name)
        cls.ac = AdmissionConditionFactory(education_group_year=egy)
        common_egy = EducationGroupYearCommonBachelorFactory(academic_year=egy.academic_year)
        AdmissionConditionFactory(education_group_year=common_egy)
        cls.serializer = BachelorAdmissionConditionsSerializer(cls.ac, context={
            'lang': settings.LANGUAGE_CODE_EN,
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'alert_message',
            'ca_bacs_cond_generales',
            'ca_bacs_cond_particulieres',
            'ca_bacs_examen_langue',
            'ca_bacs_cond_speciales'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)


class SpecializedMasterAdmissionConditionsSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        egy = EducationGroupYearFactory(education_group_type__name=TrainingType.MASTER_MC.name)
        cls.ac = AdmissionConditionFactory(education_group_year=egy)
        common_egy = EducationGroupYearCommonSpecializedMasterFactory(academic_year=egy.academic_year)
        AdmissionConditionFactory(education_group_year=common_egy)
        cls.serializer = SpecializedMasterAdmissionConditionsSerializer(cls.ac, context={
            'lang': settings.LANGUAGE_CODE_EN,
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'free_text',
            'alert_message',
            'ca_cond_generales',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)


class AggregationAdmissionConditionsSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        egy = EducationGroupYearFactory(education_group_type__name=TrainingType.AGGREGATION.name)
        cls.ac = AdmissionConditionFactory(education_group_year=egy)
        common_egy = EducationGroupYearCommonAgregationFactory(academic_year=egy.academic_year)
        AdmissionConditionFactory(education_group_year=common_egy)
        cls.serializer = AggregationAdmissionConditionsSerializer(cls.ac, context={
            'lang': settings.LANGUAGE_CODE_EN,
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'free_text',
            'alert_message',
            'ca_cond_generales',
            'ca_maitrise_fr',
            'ca_allegement',
            'ca_ouv_adultes'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)


class MasterAdmissionConditionsSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        egy = TrainingFactory(education_group_type__name=TrainingType.PGRM_MASTER_120.name)
        cls.ac = AdmissionConditionFactory(education_group_year=egy)
        common_egy = EducationGroupYearCommonMasterFactory(academic_year=egy.academic_year)
        AdmissionConditionFactory(education_group_year=common_egy)
        cls.serializer = MasterAdmissionConditionsSerializer(cls.ac, context={
            'lang': settings.LANGUAGE_CODE_EN,
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'free_text',
            'alert_message',
            'sections',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_ensure_sections_is_a_dict(self):
        self.assertEqual(type(self.serializer.data['sections']), dict)
        expected_fields = [
            'admission_enrollment_procedures',
            'non_university_bachelors',
            'holders_non_university_second_degree',
            'adults_taking_up_university_training',
            'personalized_access',
            'university_bachelors',
            'holders_second_university_degree'
        ]

        self.assertCountEqual(list(self.serializer.data['sections'].keys()), expected_fields)

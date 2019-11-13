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
from base.tests.factories.admission_condition import AdmissionConditionFactory, AdmissionConditionLineFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, EducationGroupYearCommonMasterFactory
from webservices.api.serializers.admission_condition_line import AdmissionConditionTextsSerializer, \
    AdmissionConditionLineSerializer


class AdmissionConditionTextsSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        egy = EducationGroupYearFactory(education_group_type__name=TrainingType.PGRM_MASTER_120.name)
        cls.ac = AdmissionConditionFactory(education_group_year=egy)
        common_egy = EducationGroupYearCommonMasterFactory(academic_year=egy.academic_year)
        AdmissionConditionFactory(education_group_year=common_egy)
        cls.serializer = AdmissionConditionTextsSerializer(cls.ac, context={
            'lang': settings.LANGUAGE_CODE_EN,
            'section': 'personalized_access'
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'text',
            'text_common',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)


class AdmissionConditionlineSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.acl = AdmissionConditionLineFactory()
        cls.serializer = AdmissionConditionLineSerializer(cls.acl, context={
            'lang': settings.LANGUAGE_CODE_EN,
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'access',
            'conditions',
            'diploma',
            'remarks'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

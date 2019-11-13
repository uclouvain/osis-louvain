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

from base.business.education_groups import general_information_sections
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.admission_condition import AdmissionConditionFactory
from base.tests.factories.education_group_year import EducationGroupYearCommonBachelorFactory, \
    EducationGroupYearCommonMasterFactory, \
    EducationGroupYearCommonSpecializedMasterFactory, EducationGroupYearCommonAgregationFactory
from webservices.api.serializers.common_admission_condition import CommonAdmissionConditionSerializer


class CommonAdmissionConditionSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.language = settings.LANGUAGE_CODE_EN
        cls.anac = AcademicYearFactory()
        common_ba = EducationGroupYearCommonBachelorFactory(academic_year=cls.anac)
        common_m = EducationGroupYearCommonMasterFactory(academic_year=cls.anac)
        common_mc = EducationGroupYearCommonSpecializedMasterFactory(academic_year=cls.anac)
        common_2a = EducationGroupYearCommonAgregationFactory(academic_year=cls.anac)
        cls.common_egy = [common_ba, common_m, common_mc, common_2a]
        cls.data = {}
        for egy in cls.common_egy:
            ac = AdmissionConditionFactory(education_group_year=egy)
            relevant_attr = general_information_sections.COMMON_TYPE_ADMISSION_CONDITIONS[
                egy.education_group_type.name
            ]
            cls.data[egy.acronym] = {
                field: getattr(ac, 'text_{}{}'.format(field, '_en')) or None
                for field in relevant_attr
            }

        cls.serializer = CommonAdmissionConditionSerializer(cls.data, context={'language': cls.language})

    def test_contains_expected_fields(self):
        expected_fields = [
            'common-1ba',
            'common-2m',
            'common-2mc',
            'common-2a',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_each_common_contains_expected_fields(self):
        for egy in self.common_egy:
            expected_fields = general_information_sections.COMMON_TYPE_ADMISSION_CONDITIONS[
                egy.education_group_type.name
            ]
            self.assertCountEqual(list(self.serializer.data[egy.acronym].keys()), list(expected_fields))

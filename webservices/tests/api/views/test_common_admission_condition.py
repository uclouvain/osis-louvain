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
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.business.education_groups import general_information_sections
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.admission_condition import AdmissionConditionFactory
from base.tests.factories.education_group_year import EducationGroupYearCommonBachelorFactory, \
    EducationGroupYearCommonMasterFactory, \
    EducationGroupYearCommonSpecializedMasterFactory, EducationGroupYearCommonAgregationFactory
from base.tests.factories.person import PersonFactory
from webservices.api.serializers.common_admission_condition import CommonAdmissionConditionSerializer
from webservices.api.views.common_admission_condition import CommonAdmissionCondition


class CommonAdmissionConditionTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
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
        cls.url = reverse(CommonAdmissionCondition.name, kwargs={
            'year': cls.anac.year,
            'language': cls.language
        })

    def setUp(self):
        self.client.force_authenticate(user=self.person.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_results_case_education_group_year_not_found(self):
        invalid_url = reverse('commonadmissionconditions_read', kwargs={
            'year': self.anac.year + 1,
            'language': settings.LANGUAGE_CODE_EN
        })
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = CommonAdmissionConditionSerializer(self.data, context={'language': self.language})
        self.assertEqual(response.data, serializer.data)

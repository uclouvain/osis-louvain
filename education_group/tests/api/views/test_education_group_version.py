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
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory
from base.tests.factories.user import UserFactory
from education_group.api.serializers.education_group_version import VersionListSerializer
from education_group.api.views.education_group_version import TrainingVersionList, MiniTrainingVersionList
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.models.education_group_version import EducationGroupVersion
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory, \
    StandardEducationGroupVersionFactory, StandardTransitionEducationGroupVersionFactory


class TrainingVersionListTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)

        cls.offer = TrainingFactory(academic_year=cls.academic_year)
        cls.versions = []
        for _ in range(4):
            cls.versions.append(EducationGroupVersionFactory(offer=cls.offer))
        cls.user = UserFactory()
        cls.url = reverse('education_group_api_v1:' + TrainingVersionList.name, kwargs={
            'year': cls.academic_year.year,
            'acronym': cls.offer.acronym
        })

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_result(self):
        response = self.client.get(self.url)

        serializer = VersionListSerializer(self.versions, many=True, context={
            'request': RequestFactory().get(self.url),
            'language': settings.LANGUAGE_CODE_FR
        })
        self.assertCountEqual(response.data['results'], serializer.data)


class MiniTrainingVersionListTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)

        cls.offer = TrainingFactory(academic_year=cls.academic_year)
        cls.versions = []
        cls.partial_acronym = 'LHIST100I'
        group = GroupYearFactory(
            academic_year=cls.academic_year,
            partial_acronym=cls.partial_acronym,
            group__start_year=cls.academic_year
        )
        cls.versions.append(StandardEducationGroupVersionFactory(offer=cls.offer, root_group=group))
        group_transition = GroupYearFactory(
            academic_year=cls.academic_year,
            partial_acronym=cls.partial_acronym,
            group__start_year=cls.academic_year
        )
        cls.versions.append(
            StandardTransitionEducationGroupVersionFactory(offer=cls.offer, root_group=group_transition)
        )
        cls.user = UserFactory()
        cls.url = reverse('education_group_api_v1:' + MiniTrainingVersionList.name, kwargs={
            'year': cls.academic_year.year,
            'partial_acronym': cls.partial_acronym
        })

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_result(self):
        response = self.client.get(self.url)

        serializer = VersionListSerializer(self.versions, many=True, context={
            'request': RequestFactory().get(self.url),
            'language': settings.LANGUAGE_CODE_FR
        })
        self.assertCountEqual(response.data['results'], serializer.data)


class FilterVersionTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

        cls.offer = TrainingFactory()
        cls.versions = [
            StandardTransitionEducationGroupVersionFactory(offer=cls.offer),
            StandardEducationGroupVersionFactory(offer=cls.offer)
        ]
        cls.url = reverse('education_group_api_v1:' + TrainingVersionList.name, kwargs={
            'year': cls.offer.academic_year.year,
            'acronym': cls.offer.acronym
        })

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_version_case_params_is_transition_false(self):
        query_string = {'is_transition': 'false'}

        response = self.client.get(self.url, data=query_string)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        trainings = EducationGroupVersion.objects.filter(is_transition=False)

        serializer = VersionListSerializer(
            trainings,
            many=True,
            context={'request': RequestFactory().get(self.url, query_string)},
        )
        self.assertEqual(response.data['results'], serializer.data)

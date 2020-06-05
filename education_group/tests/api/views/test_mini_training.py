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
import urllib.parse

from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.models.enums import organization_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import MiniTrainingFactory, TrainingFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from education_group.api.serializers.education_group_title import EducationGroupTitleSerializer
from education_group.api.serializers.mini_training import MiniTrainingDetailSerializer, MiniTrainingListSerializer
from education_group.api.views.mini_training import MiniTrainingList, OfferRoots


class MiniTrainingTitleTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        anac = AcademicYearFactory()

        cls.egy = MiniTrainingFactory(academic_year=anac)

        cls.person = PersonFactory()
        cls.url = reverse('education_group_api_v1:minitrainingstitle_read', kwargs={
            'partial_acronym': cls.egy.partial_acronym,
            'year': cls.egy.academic_year.year
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
        invalid_url = reverse('education_group_api_v1:minitrainingstitle_read', kwargs={
            'partial_acronym': 'ACRO',
            'year': 2019
        })
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = EducationGroupTitleSerializer(self.egy, context={'language': settings.LANGUAGE_CODE})
        self.assertEqual(response.data, serializer.data)


class MiniTrainingListTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.entity_version = EntityVersionFactory(entity__organization__type=organization_type.MAIN)

        cls.mini_trainings = []
        for partial_acronym in ['LLOGO210O', 'NLOGO2101', 'WLOGO2102']:
            cls.mini_trainings.append(
                MiniTrainingFactory(
                    partial_acronym=partial_acronym,
                    academic_year=cls.academic_year,
                    management_entity=cls.entity_version.entity,
                )
            )
        cls.user = UserFactory()
        cls.url = reverse('education_group_api_v1:' + MiniTrainingList.name)

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

    def test_get_filter_by_multiple_education_group_type(self):
        """
        This test ensure that multiple filtering by education_group_type will act as an OR
        """
        url = self.url + "?" + urllib.parse.urlencode({
            'education_group_type': [mini_training.education_group_type.name for mini_training in self.mini_trainings]
        }, doseq=True)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_get_filter_by_code(self):
        url = self.url + "?" + urllib.parse.urlencode({
            'code': self.mini_trainings[1].partial_acronym
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['code'], self.mini_trainings[1].partial_acronym)

    def test_get_filter_by_acronym(self):
        url = self.url + "?" + urllib.parse.urlencode({
            'acronym': self.mini_trainings[0].acronym
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_filter_from_year_to_year(self):
        MiniTrainingFactory(academic_year__year=self.academic_year.year - 1)
        MiniTrainingFactory(academic_year__year=self.academic_year.year + 1)

        url = self.url + "?" + urllib.parse.urlencode({
            'from_year': self.academic_year.year,
            'to_year': self.academic_year.year
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_order_by_code_in_reverse(self):
        url = self.url + "?" + urllib.parse.urlencode({
            'ordering': '-code'
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['code'], self.mini_trainings[2].partial_acronym)
        self.assertEqual(response.data['results'][1]['code'], self.mini_trainings[1].partial_acronym)
        self.assertEqual(response.data['results'][2]['code'], self.mini_trainings[0].partial_acronym)

    def test_get_training_case_filter_lowercase_acronym(self):
        query_string = {'partial_acronym': self.mini_trainings[1].partial_acronym.lower()}

        response = self.client.get(self.url, data=query_string)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = MiniTrainingListSerializer(
            self.mini_trainings[1],
            context={
                'request': RequestFactory().get(self.url, query_string),
                'language': settings.LANGUAGE_CODE_FR
            },
        )
        self.assertEqual(dict(response.data['results'][0]), serializer.data)


class GetMiniTrainingTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.mini_training = MiniTrainingFactory(partial_acronym='LGENR100I', academic_year=cls.academic_year)

        cls.user = UserFactory()
        cls.url = reverse('education_group_api_v1:mini_training_read', kwargs={
            'partial_acronym': cls.mini_training.partial_acronym,
            'year': cls.academic_year.year
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

    def test_get_valid_mini_training(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = MiniTrainingDetailSerializer(
            self.mini_training,
            context={
                'request': RequestFactory().get(self.url),
                'language': settings.LANGUAGE_CODE_FR
            },
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid_mini_training_case_not_found(self):
        invalid_url = reverse('education_group_api_v1:mini_training_read', kwargs={
            'partial_acronym': 'ACRO',
            'year': 2033
        })
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OfferRootsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.entity_version = EntityVersionFactory(entity__organization__type=organization_type.MAIN)

        cls.minor = MiniTrainingFactory(academic_year=cls.academic_year)
        for _ in range(0, 3):
            offer = TrainingFactory(academic_year=cls.academic_year)
            GroupElementYearFactory(parent=offer, child_branch=cls.minor, child_leaf=None)
        cls.user = UserFactory()
        cls.url = reverse('education_group_api_v1:' + OfferRoots.name, kwargs={
            'partial_acronym': cls.minor.partial_acronym,
            'year': cls.academic_year.year
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

    def test_get_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

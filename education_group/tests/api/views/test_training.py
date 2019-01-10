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
import uuid

from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.settings import api_settings
from rest_framework.test import APITestCase

from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory
from base.tests.factories.user import UserFactory
from education_group.api.serializers.training import TrainingListSerializer, TrainingDetailSerializer


class GetAllTrainingTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse('education_group_api_v1:training-list')

        cls.academic_year = AcademicYearFactory(year=2018)
        TrainingFactory(acronym='BIR1BA', partial_acronym='LBIR1000I', academic_year=cls.academic_year)
        TrainingFactory(acronym='AGRO1BA', partial_acronym='LAGRO2111C', academic_year=cls.academic_year)
        TrainingFactory(acronym='MED12M', partial_acronym='LMED12MA', academic_year=cls.academic_year)

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_all_training_ensure_response_have_next_previous_results_count(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue('previous' in response.data)
        self.assertTrue('next' in response.data)
        self.assertTrue('results' in response.data)

        self.assertTrue('count' in response.data)
        expected_count = EducationGroupYear.objects.filter(
            education_group_type__category=education_group_categories.TRAINING,
        ).count()
        self.assertEqual(response.data['count'], expected_count)

    def test_get_all_training_ensure_default_order(self):
        """ This test ensure that default order is academic_year [DESC Order] + acronym [ASC Order]"""
        TrainingFactory(acronym='BIR1BA', partial_acronym='LBIR1000I', academic_year__year=2017)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        trainings = EducationGroupYear.objects.filter(
            education_group_type__category=education_group_categories.TRAINING,
        ).order_by('-academic_year__year', 'acronym')
        serializer = TrainingListSerializer(trainings, many=True, context={'request': RequestFactory().get(self.url)})
        self.assertEqual(response.data['results'], serializer.data)

    def test_get_all_training_specify_ordering_field(self):
        ordering_managed = ['acronym', 'partial_acronym', 'title', 'title_english']

        for order in ordering_managed:
            query_string = {api_settings.ORDERING_PARAM: order}
            response = self.client.get(self.url, kwargs=query_string)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            trainings = EducationGroupYear.objects.filter(
                education_group_type__category=education_group_categories.TRAINING,
            ).order_by(order)
            serializer = TrainingListSerializer(
                trainings,
                many=True,
                context={'request': RequestFactory().get(self.url, query_string)},
            )
            self.assertEqual(response.data['results'], serializer.data)


class GetTrainingTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.training = TrainingFactory(acronym='BIR1BA', partial_acronym='LBIR1000I', academic_year=cls.academic_year)

        cls.user = UserFactory()
        cls.url = reverse('education_group_api_v1:training-detail', kwargs={'uuid': cls.training.uuid})

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_valid_training(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = TrainingDetailSerializer(
            self.training,
            context={'request': RequestFactory().get(self.url)},
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid_training_case_not_found(self):
        invalid_url = reverse('education_group_api_v1:training-detail', kwargs={'uuid':  uuid.uuid4()})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

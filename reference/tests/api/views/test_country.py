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
import uuid

from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.settings import api_settings
from rest_framework.test import APITestCase

from base.tests.factories.user import UserFactory
from reference.api.serializers.country import CountrySerializer
from reference.models.country import Country
from reference.tests.factories.country import CountryFactory


class GetAllCountryTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse('reference_api_v1:country-list')

        CountryFactory(iso_code='BE')
        CountryFactory(iso_code='FR')
        CountryFactory(iso_code='UK')

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

    def test_get_all_country_ensure_response_have_next_previous_results_count(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue('previous' in response.data)
        self.assertTrue('next' in response.data)
        self.assertTrue('results' in response.data)

        self.assertTrue('count' in response.data)
        expected_count = Country.objects.all().count()
        self.assertEqual(response.data['count'], expected_count)

    def test_get_all_country_ensure_default_order(self):
        """ This test ensure that default order is name [ASC Order]"""

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results_sorted = sorted(response.data["results"], key=lambda obj: obj["name"])
        self.assertListEqual(response.data["results"], results_sorted)

    def test_get_all_country_specify_ordering_field(self):
        ordering_managed = ['name', 'iso_code']

        for order_field in ordering_managed:
            with self.subTest(order_field=order_field):
                query_string = {api_settings.ORDERING_PARAM: order_field}
                response = self.client.get(self.url, kwargs=query_string)
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                results_sorted = sorted(response.data["results"], key=lambda obj: obj[order_field])
                self.assertListEqual(response.data["results"], results_sorted)


class GetCountryTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.country = CountryFactory()

        cls.user = UserFactory()
        cls.url = reverse('reference_api_v1:country-detail', kwargs={'uuid': cls.country.uuid})

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

    def test_get_valid_country(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = CountrySerializer(
            self.country,
            context={'request': RequestFactory().get(self.url)},
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid_country_case_not_found(self):
        invalid_url = reverse('reference_api_v1:country-detail', kwargs={'uuid':  uuid.uuid4()})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

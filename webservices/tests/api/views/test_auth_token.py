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
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from base.tests.factories.user import UserFactory
from webservices.api.views.auth_token import AuthToken


class AuthTokenTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserFactory(is_staff=True)
        cls.url = reverse(AuthToken.name)

    def setUp(self):
        self.user_who_want_token = UserFactory()
        self.client.force_authenticate(user=self.admin_user)

    def test_auth_token_without_credentials(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_token_method_not_allowed(self):
        methods_not_allowed = ['get', 'delete', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_auth_token_case_only_admin_have_permission(self):
        non_admin_user = UserFactory(is_staff=False)
        self.client.force_authenticate(user=non_admin_user)
        response = self.client.post(self.url, data={'username': self.user_who_want_token.username})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.url, data={'username': self.user_who_want_token.username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_auth_token_case_username_not_exist(self):
        response = self.client.post(self.url, data={'username': 'dummy-username'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        expected_data = {'username': [ErrorDetail(_('Unable to find username provided.'), code='invalid')]}
        self.assertDictEqual(response.data, expected_data)

    def test_auth_token_case_missing_required_args(self):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_auth_token_case_success_ensure_response(self):
        response = self.client.post(self.url, data={'username': self.user_who_want_token.username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token_generated = Token.objects.get(user=self.user_who_want_token)
        self.assertEqual(response.data['token'], token_generated.key)

    def test_auth_token_ensure_multiple_call_dont_regenerate_token(self):
        response = self.client.post(self.url, data={'username': self.user_who_want_token.username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_2 = self.client.post(self.url, data={'username': self.user_who_want_token.username})
        self.assertEqual(response_2.status_code, status.HTTP_200_OK)

        self.assertDictEqual(response.data, response_2.data)

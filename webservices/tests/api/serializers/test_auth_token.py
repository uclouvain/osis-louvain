##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth import backends
from django.test import TestCase
from rest_framework import serializers

from base.tests.factories.user import UserFactory
from webservices.api.serializers.auth_token import AuthTokenSerializer


class AuthTokenSerializerTestCase(TestCase):
    def test_serializer_case_username_required(self):
        serializer = AuthTokenSerializer(data={})
        self.assertFalse(serializer.is_valid())

    def test_serializer_case_username_not_exist(self):
        serializer = AuthTokenSerializer(data={'username': 'dummy-username'})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_serializer_case_username_not_exist_with_force_create(self):
        serializer = AuthTokenSerializer(data={'username': 'dummy-username', 'force_user_creation': True})
        self.assertTrue(serializer.is_valid())

        UserModel = backends.get_user_model()
        user_created = serializer.validated_data['user']
        self.assertEqual(
            'dummy-username',
            getattr(user_created, UserModel.USERNAME_FIELD)
        )

    def test_serializer_case_success_ensure_user(self):
        user = UserFactory()
        serializer = AuthTokenSerializer(data={'username': user.username})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], user)

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
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.api.serializers.person import PersonRolesSerializer
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory


class GetPersonRolesTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory(global_id=4215)
        for _ in range(2):
            entity = EntityFactory()
            EntityVersionFactory(entity=entity)
            PersonEntityFactory(
                person=cls.person,
                entity=entity
            )

        cls.user = UserFactory()
        cls.url = reverse('base_api_v1:person-roles', kwargs={'global_id': cls.person.global_id})

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

    def test_get_valid_person_roles(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = PersonRolesSerializer(
            self.person,
            context={'request': RequestFactory().get(self.url)},
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid_person_case_not_found(self):
        invalid_url = reverse('base_api_v1:person-roles', kwargs={'global_id':  6666})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

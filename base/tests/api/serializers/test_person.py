##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase

from base.api.serializers.person import PersonDetailSerializer, PersonRolesSerializer
from base.tests.factories.person import PersonFactory
from education_group.auth.scope import Scope
from education_group.tests.factories.auth.central_manager import CentralManagerFactory


class PersonDetailSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.serializer = PersonDetailSerializer(cls.person)

    def test_contains_expected_fields(self):
        expected_fields = [
            'first_name',
            'last_name',
            'email',
            'gender',
            'uuid',
            'birth_date'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)


class PersonRolesSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.serializer = PersonRolesSerializer(cls.person)

    def test_contains_expected_fields(self):
        expected_fields = [
            'global_id',
            'roles'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_get_person_roles_assert_iufc_scope(self):
        CentralManagerFactory(person=self.person, scopes=[Scope.IUFC.name])

        serializer = PersonRolesSerializer(self.person)
        self.assertIn(Scope.IUFC.name, serializer.data['roles']['reddot']['scope'])

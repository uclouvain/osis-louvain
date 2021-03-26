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
import datetime

from django.test import TestCase

from base.models.enums import organization_type, entity_type
from base.tests.factories import campus as campus_factory, organization as organization_factory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from education_group.auth.roles.central_manager import CentralManager as CentralManagerEG
from education_group.tests.factories.auth.central_manager import CentralManagerFactory as CentralManagerEGFactory
from learning_unit.auth.roles.central_manager import CentralManager as CentralManagerLU
from learning_unit.tests.factories.central_manager import CentralManagerFactory as CentralManagerLUFactory
from osis_role.contrib.helper import EntityRoleHelper


class TestRoleModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = organization_factory.OrganizationFactory(type=organization_type.MAIN)
        cls.campus = campus_factory.CampusFactory(organization=cls.organization, is_administration=True)
        cls.entity = EntityFactory(organization=cls.organization)
        cls.entity_version = EntityVersionFactory(
            entity=cls.entity, entity_type=entity_type.FACULTY,
            start_date=datetime.date.today().replace(year=1900), end_date=None
        )
        cls.central_manager_for_eg = CentralManagerEGFactory(entity=cls.entity)
        cls.central_manager_for_lu = CentralManagerLUFactory(entity=cls.entity)
        cls.central_manager_full = CentralManagerEGFactory(entity=cls.entity)
        CentralManagerLUFactory(entity=cls.entity, person=cls.central_manager_full.person)

    def test_get_all_entities(self):
        cases = [
            {
                'name': 'Central manager EG',
                'value_to_test': EntityRoleHelper.get_all_entities(self.central_manager_for_eg.person,
                                                                   {CentralManagerEG.group_name}),
                'expected_value': {self.entity.id}
            },
            {
                'name': 'Central manager LU',
                'value_to_test': EntityRoleHelper.get_all_entities(self.central_manager_for_lu.person,
                                                                   {CentralManagerLU.group_name}),
                'expected_value': {self.entity.id}
            }
        ]
        for case in cases:
            with self.subTest(case['name']):
                self.assertEqual(case['value_to_test'], case['expected_value'])

    def test_get_all_roles(self):
        cases = [
            {
                'name': 'Central manager EG',
                'value_to_test': EntityRoleHelper.get_all_roles(self.central_manager_for_eg.person),
                'expected_value': [CentralManagerEG]
            },
            {
                'name': 'Central manager LU',
                'value_to_test': EntityRoleHelper.get_all_roles(self.central_manager_for_lu.person),
                'expected_value': [CentralManagerLU]
            },
            {
                'name': 'Central manager FULL',
                'value_to_test': EntityRoleHelper.get_all_roles(self.central_manager_full.person),
                'expected_value': [CentralManagerLU, CentralManagerEG]
            }
        ]

        for case in cases:
            with self.subTest(case['name']):
                self.assertCountEqual(case['value_to_test'], case['expected_value'])
                for value in case['value_to_test']:
                    self.assertIn(value, case['expected_value'])

    def test_has_roles(self):
        cases = [
            {
                'name': 'Central manager EG',
                'person': self.central_manager_for_eg.person,
                'role': [CentralManagerEG],
                'expected_value': True
            },
            {
                'name': 'Central manager LU without EG',
                'person': self.central_manager_for_lu.person,
                'role': [CentralManagerLU, CentralManagerEG],
                'expected_value': False
            },
            {
                'name': 'Central manager FULL',
                'person': self.central_manager_full.person,
                'role': [CentralManagerLU, CentralManagerEG],
                'expected_value': True
            }
        ]
        for case in cases:
            with self.subTest(case['name']):
                self.assertEqual(
                    EntityRoleHelper.has_roles(case['person'], case['role']), case['expected_value']
                )

    def test_has_role(self):
        cases = [
            {
                'name': 'Central manager EG',
                'person': self.central_manager_for_eg.person,
                'role': CentralManagerEG,
                'expected_value': True
            },
            {
                'name': 'Central manager LU',
                'person': self.central_manager_for_lu.person,
                'role': CentralManagerLU,
                'expected_value': True
            },
            {
                'name': 'Central manager FULL with 1 role',
                'person': self.central_manager_full.person,
                'role': CentralManagerLU,
                'expected_value': True
            },
            {
                'name': 'Central manager LU with wrong value',
                'person': self.central_manager_for_lu.person,
                'role': CentralManagerEG,
                'expected_value': False
            }
        ]

        for case in cases:
            with self.subTest(case['name']):
                self.assertEqual(
                    EntityRoleHelper.has_role(case['person'], case['role']), case['expected_value']
                )

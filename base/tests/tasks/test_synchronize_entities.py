# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import datetime

import mock
from django.test import TestCase

from base.models.entity_version import EntityVersion
from base.models.entity_version_address import EntityVersionAddress
from base.models.enums import entity_type
from base.tasks import synchronize_entities
from base.tasks.synchronize_entities import FetchEntitiesException
from base.tests.factories.organization import MainOrganizationFactory
from reference.tests.factories.country import CountryFactory


class TestSynchronizeEntities(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.main_organization = MainOrganizationFactory()
        cls.belgium = CountryFactory(iso_code="BE")

    def setUp(self) -> None:
        self.fetch_entities_patcher = mock.patch(
            "base.tasks.synchronize_entities.__fetch_entities_from_esb",
            return_value=_mock_fetch_entities_from_esb_return_value()
        )
        self.mocked_fetch_entities = self.fetch_entities_patcher.start()
        self.addCleanup(self.fetch_entities_patcher.stop)

        self.fetch_address_patcher = mock.patch(
            "base.tasks.synchronize_entities.__fetch_address_from_esb",
            return_value=_mock_fetch_address_from_esb_return_value()
        )
        self.mocked_fetch_address = self.fetch_address_patcher.start()
        self.addCleanup(self.fetch_address_patcher.stop)

    def test_synchronize_entities_assert_entity_version(self):
        synchronize_entities.run()

        root_entity = EntityVersion.objects.get(acronym='UCL', parent__isnull=True)
        self.assertEqual(root_entity.start_date, datetime.date(year=2010, month=1, day=1))
        self.assertIsNone(root_entity.end_date)
        self.assertEqual(root_entity.title, "Secteur UCL")
        self.assertEqual(root_entity.entity_type, "")
        self.assertEqual(root_entity.entity.external_id, 'osis.entity_01000000')
        self.assertEqual(root_entity.entity.fax, "0888888888")
        self.assertEqual(root_entity.entity.phone, "099999999")

        child = EntityVersion.objects.get(acronym='AS', parent=root_entity.entity)
        self.assertEqual(child.start_date, datetime.date(year=2010, month=1, day=1))
        self.assertIsNone(child.end_date)
        self.assertEqual(child.title, "Autorités et services")
        self.assertEqual(child.entity_type, entity_type.LOGISTICS_ENTITY)
        self.assertEqual(child.entity.external_id, 'osis.entity_01000472')

    def test_synchronize_entities_assert_entity_version_address(self):
        synchronize_entities.run()

        address = EntityVersionAddress.objects.get(
            entity_version__acronym='UCL',
            entity_version__parent__isnull=True,
            is_main=True
        )
        self.assertEqual(address.country, self.belgium)
        self.assertEqual(address.street, "Place Montesquieu")
        self.assertEqual(address.street_number, '2')
        self.assertEqual(address.postal_code, '1348')
        self.assertEqual(address.city, "Louvain-la-Neuve")

    def test_synchronize_entities_assert_exception_raised_display_error(self):
        self.mocked_fetch_entities.side_effect = FetchEntitiesException

        result = synchronize_entities.run()
        self.assertEqual(result, {'Entities synchronized': 'Unable to fetch data from ESB'})


def _mock_fetch_entities_from_esb_return_value():
    return [
        {
            "begin": 20100101,
            "end": 99991231,
            "entity_id": "01000000",
            "acronym": "UCL",
            "acronyms": None,
            "fullAcronym": "UCL",
            "departmentType": "N",
            "name_fr": "Secteur UCL",
            "name_en": None,
            "parent_entity_id": {
               "@nil": "true"
            },
            "web": None
        },
        {
            "begin": 20100101,
            "end": 99991231,
            "entity_id": "01000472",
            "acronym": "AS",
            "acronyms": "AS",
            "fullAcronym": "AS",
            "departmentType": "L",
            "name_fr": "Autorités et services",
            "name_en": None,
            "parent_entity_id": "01000000",
            "web": None
        }
    ]


def _mock_fetch_address_from_esb_return_value():
    return {
        "code": "SH03",
        "build": "Collège Thomas More",
        "streetName": "Place Montesquieu",
        "streetNumber": 2,
        "mailBox": "L2.07.01",
        "postCode": 1348,
        "town": "Louvain-la-Neuve",
        "phone": "099999999",
        "fax": "0888888888"
    }

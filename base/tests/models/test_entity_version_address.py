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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.db import IntegrityError
from django.test import TestCase

from base.tests.factories.entity_version_address import EntityVersionAddressFactory


class EntityVersionAddressTest(TestCase):
    def test_create_addresses_with_same_entity_version_id_and_is_main_true(self):
        address = EntityVersionAddressFactory(is_main=True)
        with self.assertRaises(IntegrityError):
            EntityVersionAddressFactory(
                is_main=True,
                entity_version_id=address.entity_version_id
            )

    def test_update_address_with_same_entity_version_id_and_is_main_true(self):
        address_1 = EntityVersionAddressFactory(is_main=True)
        address_2 = EntityVersionAddressFactory(
            is_main=False,
            entity_version_id=address_1.entity_version_id,
        )

        with self.assertRaises(IntegrityError):
            address_2.is_main = True
            address_2.save()

    def test_update_address(self):
        address = EntityVersionAddressFactory(is_main=True)
        address.street_number = 17
        address.save()
        self.assertEquals(address.street_number, 17)

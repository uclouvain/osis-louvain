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

from django.test import TestCase

from base.models import person_address
from base.models.enums import person_address_type
from base.tests.factories import user
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_address import PersonAddressFactory


class PersonAddressTestCase(TestCase):
    def setUp(self):
        self.a_user = user.UserFactory(username="user_with_person")
        self.a_person = PersonFactory(user=self.a_user, language="fr-be", first_name="John", last_name="Doe")
        self.address = PersonAddressFactory(person=self.a_person)

    def test_default_label(self):
        self.assertEqual(self.address.label, person_address_type.PersonAddressType.PROFESSIONAL.value)

    def test_find_by_person(self):
        addresses = person_address.find_by_person(self.a_person)

        for address in addresses:
            self.assertEqual(address.person, self.a_person)

    def test_get_by_label(self):
        address = person_address.get_by_label(self.a_person, person_address_type.PersonAddressType.RESIDENTIAL.value)
        self.assertIsNone(address)

        address = person_address.get_by_label(self.a_person, person_address_type.PersonAddressType.PROFESSIONAL.value)
        self.assertEqual(address.person, self.a_person)
        self.assertEqual(address.label, person_address_type.PersonAddressType.PROFESSIONAL.value)

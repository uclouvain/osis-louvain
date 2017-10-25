##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.urlresolvers import reverse
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.organization_address import OrganizationAddressFactory
from base.tests.factories.user import SuperUserFactory


class OrganizationViewTestCase(TestCase):

    def setUp(self):
        self.organization = OrganizationFactory()
        self.a_superuser = SuperUserFactory()
        self.client.force_login(self.a_superuser)

    def test_organization_save(self):
        url = reverse('organization_save', args=[self.organization.id])
        response = self.client.post(url, data=get_form_organization_save())
        self.organization.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.organization.acronym, "NYU")
        self.assertEqual(self.organization.name, "NEW-YORK UNIVERSITY")

    def test_organization_address_save(self):
        address = OrganizationAddressFactory(organization=self.organization)
        country = address.country
        url = reverse('organization_address_save', args=[address.id])
        response = self.client.post(url, data=get_form_organization_address_save())
        address.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(address.location, "476 5th Ave")
        self.assertEqual(address.postal_code, "10018")
        self.assertEqual(address.city, "New York")
        self.assertEqual(address.country, country)


def get_form_organization_save():
    return {
        "acronym": "NYU",
        "name": "NEW-YORK UNIVERSITY",
        "website": "www.nyu.edu",
        "prefix": "NYUA"
    }


def get_form_organization_address_save():
    return {
        "organization_address_label": "Building",
        "organization_address_location": "476 5th Ave",
        "organization_address_postal_code": "10018",
        "organization_address_city": "New York"
    }

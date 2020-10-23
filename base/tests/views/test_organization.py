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
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.urls import reverse

from base.models import organization_address
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.organization_address import OrganizationAddressFactory
from base.tests.factories.user import SuperUserFactory
from base.views.organization import organization_address_delete


class OrganizationViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory()
        cls.entity = EntityFactory(organization=cls.organization)
        cls.entity_version = EntityVersionFactory(entity=cls.entity)
        cls.a_superuser = SuperUserFactory()

    def setUp(self):
        self.client.force_login(self.a_superuser)

    def test_organization_address_delete(self):
        address = OrganizationAddressFactory(organization=self.organization)

        response = self.client.post(reverse(organization_address_delete, args=[address.id]))
        self.assertRedirects(response, reverse("organization_read", args=[self.organization.pk]))
        with self.assertRaises(ObjectDoesNotExist):
            organization_address.OrganizationAddress.objects.get(id=address.id)

    def test_organization_address_edit(self):
        from base.views.organization import organization_address_edit
        address = OrganizationAddressFactory(organization=self.organization)
        response = self.client.get(reverse(organization_address_edit, args=[address.id]))

        self.assertTemplateUsed(response, "organization/organization_address_form.html")
        self.assertEqual(response.context.get("organization_address"), address)

    def test_organizations_search(self):
        response = self.client.get(reverse('organizations_search'), data={
            'acronym': self.organization.acronym[:2]
        })

        self.assertTemplateUsed(response, "organization/organizations.html")
        self.assertEqual(response.context["object_list"][0], self.organization)

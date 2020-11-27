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
from django.http import HttpResponseForbidden, HttpResponse
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory, MainEntityVersionFactory
from base.tests.factories.entity_version_address import MainRootEntityVersionAddressFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.user import SuperUserFactory, UserFactory


class OrganizationSearchViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory()
        cls.entity = EntityFactory(organization=cls.organization)
        cls.entity_version = EntityVersionFactory(entity=cls.entity)
        cls.a_superuser = SuperUserFactory()

    def setUp(self):
        self.client.force_login(self.a_superuser)

    def test_organizations_search(self):
        response = self.client.get(reverse('organizations_search'), data={
            'acronym': self.organization.acronym[:2]
        })

        self.assertTemplateUsed(response, "organization/organizations.html")
        self.assertEqual(response.context["object_list"][0], self.organization)


class OrganizationDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory()
        cls.root_entity_version = MainEntityVersionFactory(
            entity__organization=cls.organization,
            parent=None
        )
        MainRootEntityVersionAddressFactory(entity_version=cls.root_entity_version)
        cls.a_superuser = SuperUserFactory()

        cls.url = reverse('organization_read', kwargs={'organization_id': cls.organization.pk})

    def setUp(self) -> None:
        self.client.force_login(self.a_superuser)

    def test_case_user_has_not_permission_assert_permission_denied(self):
        self.client.force_login(UserFactory())

        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "organization/organization.html")

    def test_assert_context_keys(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertIn('addresses', response.context)

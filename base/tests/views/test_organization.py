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
import json

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.urls import reverse

from base.models import organization_address
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.organization_address import OrganizationAddressFactory
from base.tests.factories.user import SuperUserFactory
from base.views.organization import organization_address_delete
from reference.tests.factories.country import CountryFactory


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


class TestOrganizationAutocomplete(TestCase):
    def setUp(self):
        self.super_user = SuperUserFactory()
        self.url = reverse("organization_autocomplete")

        self.organization = OrganizationFactory(name="Université de Louvain")
        self.organization_address = OrganizationAddressFactory(
            organization=self.organization,
            country__iso_code='BE',
            is_main=True
        )

    def test_when_filter_without_country_data_forwarded_result_found(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': 'univ'})

        expected_results = [{'text': self.organization.name,
                             'selected_text': self.organization.name,
                             'id': str(self.organization.pk)}]

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)

    def test_when_filter_without_country_data_forwarded_no_result_found(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': 'Grace'})

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, [])

    def test_when_filter_with_country_data_forwarded_result_found(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(
            self.url,
            data={'forward': '{"country": "%s"}' % self.organization_address.country.pk}
        )
        expected_results = [{'text': self.organization.name,
                             'selected_text': self.organization.name,
                             'id': str(self.organization.pk)}]

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)

    def test_when_filter_with_country_data_forwarded_no_result_found(self):
        country = CountryFactory(iso_code='FR')

        self.client.force_login(user=self.super_user)
        response = self.client.get(
            self.url,
            data={'forward': '{"country": "%s"}' % country.pk}
        )

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, [])

    def test_when_filter_with_country_data_forwarded_no_result_found_case_not_main(self):
        self.organization_address.is_main = False
        self.organization_address.save()

        self.client.force_login(user=self.super_user)
        response = self.client.get(
            self.url,
            data={'forward': '{"country": "%s"}' % self.organization_address.country.pk}
        )

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, [])


class TestCountryAutocomplete(TestCase):
    def setUp(self):
        self.super_user = SuperUserFactory()
        self.url = reverse("country-autocomplete")
        self.country = CountryFactory(name="Narnia")
        OrganizationAddressFactory(country=self.country)

    def test_when_filter(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': 'nar'})

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)

        expected_results = [{'text': self.country.name, 'selected_text': self.country.name, 'id': str(self.country.pk)}]

        self.assertListEqual(results, expected_results)


class TestCampusAutocomplete(TestCase):
    def setUp(self):
        self.super_user = SuperUserFactory()
        self.url = reverse("campus-autocomplete")

        self.organization = OrganizationFactory(name="Université de Louvain")
        self.organization_address = OrganizationAddressFactory(
            organization=self.organization,
            country__iso_code='BE',
            is_main=True
        )
        self.campus = CampusFactory(organization=self.organization)

    def test_when_filter_without_country_data_forwarded_result_found(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': 'univ'})

        expected_results = [{'text': "{} ({})".format(self.organization.name, self.campus.name),
                             'selected_text': "{} ({})".format(self.organization.name, self.campus.name),
                             'id': str(self.campus.pk)}]

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)

    def test_when_filter_without_country_data_forwarded_no_result_found(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': 'Grace'})

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, [])

    def test_when_filter_with_country_data_forwarded_result_found(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(
            self.url,
            data={'forward': '{"country_external_institution": "%s"}' % self.organization_address.country.pk}
        )
        expected_results = [{'text': "{} ({})".format(self.organization.name, self.campus.name),
                             'selected_text': "{} ({})".format(self.organization.name, self.campus.name),
                             'id': str(self.campus.pk)}]
        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)

    def test_when_filter_with_country_data_forwarded_no_result_found(self):
        country = CountryFactory(iso_code='FR')

        self.client.force_login(user=self.super_user)
        response = self.client.get(
            self.url,
            data={'forward': '{"country_external_institution": "%s"}' % country.pk}
        )

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, [])


def _get_results_from_autocomplete_response(response):
    json_response = str(response.content, encoding='utf8')
    return json.loads(json_response)['results']

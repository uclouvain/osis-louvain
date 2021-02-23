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
import json

from django.test import TestCase
from django.urls import reverse

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.organization_type import ACADEMIC_PARTNER, EMBASSY
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity_version_address import MainRootEntityVersionAddressFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import SuperUserFactory, UserFactory
from base.views.autocomplete import EmployeeAutocomplete
from reference.tests.factories.country import CountryFactory


class TestOrganizationAutocomplete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.super_user = SuperUserFactory()
        cls.url = reverse("organization_autocomplete")

        cls.partner_academic_organization = OrganizationFactory(type=ACADEMIC_PARTNER, name="Université de Louvain")
        cls.main_address = MainRootEntityVersionAddressFactory(
            entity_version__entity__organization=cls.partner_academic_organization,
            country__iso_code='BE',
        )

        embassy_organization = OrganizationFactory(type=EMBASSY, name="Université de Nantes")
        MainRootEntityVersionAddressFactory(
            entity_version__entity__organization=embassy_organization,
            country__iso_code='FR',
        )

    def setUp(self):
        self.client.force_login(user=self.super_user)

    def test_when_filter_without_country_data_forwarded_result_found(self):
        response = self.client.get(self.url, data={'q': 'univ'})

        expected_results = [{'text': self.partner_academic_organization.name,
                             'selected_text': self.partner_academic_organization.name,
                             'id': str(self.partner_academic_organization.pk)}]

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)

    def test_when_filter_without_country_data_forwarded_no_result_found(self):
        response = self.client.get(self.url, data={'q': 'Grace'})

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, [])

    def test_when_filter_with_country_data_forwarded_result_found(self):
        response = self.client.get(
            self.url,
            data={'forward': '{"country": "%s"}' % self.main_address.country.pk}
        )
        expected_results = [{
            'text': self.partner_academic_organization.name,
            'selected_text': self.partner_academic_organization.name,
            'id': str(self.partner_academic_organization.pk)
        }]

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)

    def test_when_filter_with_country_data_forwarded_no_result_found(self):
        country = CountryFactory(iso_code='FR')
        response = self.client.get(
            self.url,
            data={'forward': '{"country": "%s"}' % country.pk}
        )

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, [])

    def test_when_filter_with_country_data_forwarded_result_found_case_not_main(self):
        self.main_address.is_main = False
        self.main_address.save()
        response = self.client.get(
            self.url,
            data={'forward': '{"country": "%s"}' % self.main_address.country.pk}
        )

        expected_results = [{
            'text': self.partner_academic_organization.name,
            'selected_text': self.partner_academic_organization.name,
            'id': str(self.partner_academic_organization.pk)
        }]
        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)


class TestCountryAutocomplete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.super_user = SuperUserFactory()
        cls.url = reverse("country-autocomplete")
        cls.country = CountryFactory(name="Narnia")

    def test_when_filter(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': 'nar'})

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)

        expected_results = [{'text': self.country.name, 'selected_text': self.country.name, 'id': str(self.country.pk)}]

        self.assertListEqual(results, expected_results)


class TestCampusAutocomplete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.super_user = SuperUserFactory()
        cls.url = reverse("campus-autocomplete")

        cls.partner_academic_organization = OrganizationFactory(type=ACADEMIC_PARTNER, name="Université de Louvain")
        cls.main_address = MainRootEntityVersionAddressFactory(
            entity_version__entity__organization=cls.partner_academic_organization,
            country__iso_code='BE',
        )

        embassy_organization = OrganizationFactory(type=EMBASSY, name="Université de Nantes")
        MainRootEntityVersionAddressFactory(
            entity_version__entity__organization=embassy_organization,
            country__iso_code='FR',
        )

    def setUp(self):
        self.client.force_login(user=self.super_user)

    def test_when_filter_without_country_data_forwarded_result_found(self):
        response = self.client.get(self.url, data={'q': 'univ'})

        expected_results = [{
            'text': self.partner_academic_organization.name,
            'selected_text': self.partner_academic_organization.name,
            'id': str(self.partner_academic_organization.campus_set.first().pk)
        }]
        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)

    def test_when_filter_without_country_data_forwarded_no_result_found(self):
        response = self.client.get(self.url, data={'q': 'Grace'})

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, [])

    def test_when_filter_with_country_data_forwarded_result_found(self):
        response = self.client.get(
            self.url,
            data={'forward': '{"country_external_institution": "%s"}' % self.main_address.country.pk}
        )
        expected_results = [{
            'text': self.partner_academic_organization.name,
            'selected_text': self.partner_academic_organization.name,
            'id': str(self.partner_academic_organization.campus_set.first().pk)
        }]
        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)

    def test_when_filter_with_country_data_forwarded_no_result_found(self):
        country = CountryFactory(iso_code='FR')

        response = self.client.get(
            self.url,
            data={'forward': '{"country_external_institution": "%s"}' % country.pk}
        )

        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, [])


class TestPersonAutoComplete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.jean = PersonFactory(first_name="Jean", last_name="Dupont", middle_name=None, global_id="001456",
                                 employee=True)
        cls.henry = PersonFactory(first_name="Henry", last_name="Arkin", middle_name="De", global_id="002587500",
                                  employee=True)
        cls.student = PersonFactory(first_name="Henry", last_name="Dioup", middle_name=None, global_id="488513",
                                    employee=False)

    def test_get_queryset_with_name(self):
        autocomplete_instance = EmployeeAutocomplete()
        autocomplete_instance.q = self.henry.last_name

        self.assertQuerysetEqual(
            autocomplete_instance.get_queryset(),
            [self.henry],
            transform=lambda obj: obj
        )

        autocomplete_instance.q = self.jean.last_name
        self.assertQuerysetEqual(
            autocomplete_instance.get_queryset(),
            [self.jean],
            transform=lambda obj: obj
        )

    def test_get_queryset_with_global_id(self):
        autocomplete_instance = EmployeeAutocomplete()
        autocomplete_instance.q = self.henry.global_id
        self.assertQuerysetEqual(
            autocomplete_instance.get_queryset(),
            [self.henry],
            transform=lambda obj: obj
        )

        autocomplete_instance.q = self.henry.global_id.strip("0")
        self.assertQuerysetEqual(
            autocomplete_instance.get_queryset(),
            [self.henry],
            transform=lambda obj: obj
        )

    def test_get_result_label(self):
        self.assertEqual(
            EmployeeAutocomplete().get_result_label(self.jean),
            "DUPONT Jean"
        )

        self.assertEqual(
            EmployeeAutocomplete().get_result_label(self.henry),
            "ARKIN Henry"
        )


class TestAcademicCalendarTypeAutocomplete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse("academic_calendar_type_autocomplete")

    def setUp(self):
        self.client.force_login(user=self.user)

    def test_case_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_case_not_filtering_assert_all_result_provided(self):
        response = self.client.get(self.url)

        expected_results = [{'id': id, 'text': value} for id, value in AcademicCalendarTypes.choices()]
        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)

    def test_case_filtering_assert_result_return_only_filtered_element(self):
        response = self.client.get(self.url, data={'q': str(AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.value)})

        expected_results = [
            {
                'id': AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name,
                'text': AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.value
            }
        ]
        self.assertEqual(response.status_code, 200)
        results = _get_results_from_autocomplete_response(response)
        self.assertListEqual(results, expected_results)


def _get_results_from_autocomplete_response(response):
    json_response = str(response.content, encoding='utf8')
    return json.loads(json_response)['results']

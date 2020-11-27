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

from django.contrib.auth.models import Permission
from django.http.response import HttpResponseForbidden, HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity_version_address import EntityVersionAddressFactory, MainRootEntityVersionAddressFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.views.learning_units.search.common import SearchTypes
from reference.tests.factories.country import CountryFactory


class TestSearchBorrowedLearningUnits(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_unit_years = [LearningUnitYearFactory() for _ in range(5)]
        cls.person = PersonFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        cls.url = reverse("learning_units_borrowed_course")
        ac = create_current_academic_year()
        AcademicYearFactory(year=ac.year + 1)

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_user_has_not_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_get_request(self):
        response = self.client.get(self.url, data={"acronym": "acronym"})

        context = response.context
        self.assertEqual(context["search_type"], SearchTypes.BORROWED_COURSE.value)
        self.assertTemplateUsed(response, "learning_unit/search/base.html")
        self.assertEqual(len(context["object_list"]), 0)
        messages = [str(m) for m in context["messages"]]
        self.assertIn(_('No result!'), messages)


class TestSearchExternalLearningUnits(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_access_externallearningunityear"))
        cls.url = reverse("learning_units_external")
        AcademicYearFactory.produce_in_future(quantity=2)

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_user_has_not_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_get_request(self):
        response = self.client.get(self.url, data={"acronym": "acronym"})

        self.assertTemplateUsed(response, "learning_unit/search/external.html")
        context = response.context
        self.assertEqual(context["search_type"], SearchTypes.EXTERNAL_SEARCH.value)
        self.assertEqual(len(context["object_list"]), 0)
        messages = [str(m) for m in context["messages"]]
        self.assertIn(_('No result!'), messages)


class TestGetCitiesListAccordingToCountryForExternalLearningUnitsSearch(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.url = reverse("get_cities_related_to_country")

        cls.country = CountryFactory(iso_code='BE', name='Belgium')
        EntityVersionAddressFactory(city="Dinant", country=cls.country)
        EntityVersionAddressFactory(city="Namur", country=cls.country)

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

    def test_user_has_not_permission(self):
        self.client.logout()
        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_case_country_provided_is_empty_assert_return_empty(self):
        response = self.client.get(self.url, data={'country': ''}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HttpResponse.status_code)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(data), 0)

    def test_get_cities_list_according_to_country_provided(self):
        response = self.client.get(self.url, data={'country': self.country.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HttpResponse.status_code)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(data), 2)


class TestGetCampusListAccordingToCityForExternalLearningUnitsSearch(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.url = reverse("get_campuses_related_to_city")

        cls.campus_1 = CampusFactory(name="Campus 1")
        cls.main_address_campus_1 = MainRootEntityVersionAddressFactory(
            city="Dinant",
            entity_version__entity__organization=cls.campus_1.organization,
        )

        cls.campus_2 = CampusFactory(name="Campus 2")
        cls.main_address_campus_2 = MainRootEntityVersionAddressFactory(
            city="La Louvière",
            entity_version__entity__organization=cls.campus_2.organization,
        )
        cls.secondary_address_campus_2 = EntityVersionAddressFactory(
            city="Dinant",
            entity_version=cls.main_address_campus_2.entity_version,
            is_main=False
        )

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

    def test_user_has_not_permission(self):
        self.client.logout()
        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_get_campus_list_according_to_city_provided(self):
        response = self.client.get(self.url, data={'city': 'Dinant'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HttpResponse.status_code)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(data), 1)

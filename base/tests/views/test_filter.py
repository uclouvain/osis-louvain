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

from django.http import HttpResponse
from django.test import TestCase

from base.tests.factories.organization_address import OrganizationAddressFactory
from reference.tests.factories.country import CountryFactory

KWARGS = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class TestFilter(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.country = CountryFactory()

        OrganizationAddressFactory(country=cls.country, city="NAMUR")
        OrganizationAddressFactory(country=cls.country, city="DINANT")

    def test_filter_by_country(self):
        response = self.client.get('/learning_units/new/filter_cities_by_country',
                                   data={"country": self.country.id},
                                   **KWARGS
                                   )
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertEqual(str(response.content, encoding='utf8'),
                         '[{"city": "DINANT"}, {"city": "NAMUR"}]')

    def test_filter_by_country_none_selected(self):

        response = self.client.get('/learning_units/new/filter_cities_by_country',
                                   data={},
                                   **KWARGS)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertEqual(str(response.content, encoding='utf8'), '[]')

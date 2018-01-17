##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from unittest import TestCase
from reference.models import country as mdl_country
from reference.tests.factories import country


class TestCountry(TestCase):
    def test_find_by_iso_code(self):
        a_country = country.CountryFactory()
        found_country = mdl_country.get_by_iso_code(a_country.iso_code)
        self.assertEquals(a_country, found_country)

    def test_inexisting_iso_code(self):
        a_country = mdl_country.get_by_iso_code("")
        self.assertIsNone(a_country)

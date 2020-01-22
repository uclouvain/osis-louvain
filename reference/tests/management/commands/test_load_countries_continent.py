############################################################################
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
############################################################################

from django.core.management import call_command
from django.test import TestCase

from reference.models.country import Country
from reference.tests.factories.country import CountryFactory


class CommandsTestCase(TestCase):
    def test_load_countries_and_continent(self):
        CountryFactory(iso_code='BE', name='Belgium')
        args = []
        opts = {}
        call_command('load_countries_continent', *args, **opts)
        self.assertTrue(Country.objects.filter(iso_code='BE').get().continent)
        self.assertEqual(Country.objects.all().count(), 1)  # assert doesn't create any Country

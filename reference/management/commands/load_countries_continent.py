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

import csv

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from reference.models.continent import Continent
from reference.models.country import Country


class Command(BaseCommand):
    """This command links existing countries to continents. Create new Continent objects if not exists."""

    def handle(self, *args, **options):
        path = "reference/fixtures/country_and_continent_codes_list.csv"
        self.load_csv(path)

    @staticmethod
    def load_csv(path):
        with open(path, newline='') as csvfile:
            reader_iter = csv.reader(csvfile, delimiter=',', quotechar='"')
            continents = []
            for row in list(reader_iter)[1:]:  # Excluding header
                continent_name = row[0]
                continent_code = row[1]
                country_name = row[2]
                country_code = row[3]
                continents.append(continent_name)
                _set_country_continent(country_name, country_code, continent_name, continent_code)


def _set_country_continent(country_name, country_code, continent_name, continent_code):
    if continent_name:
        try:
            country = Country.objects.filter(iso_code=country_code).get()
            continent, created = Continent.objects.get_or_create(name=continent_name, code=continent_code)
            print('{} - {}'.format(country, continent))
            country.continent = continent
            country.save()
        except ObjectDoesNotExist:
            print('WARNING :: country does not exists : {}'.format(country_name))

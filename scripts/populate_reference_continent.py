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

from reference.models import continent


# Dictionnary containing all the continents. The key is the code of the
# continent.
dic_code_continent = {
    "AF": "Africa",
    "AN": "Antartica",
    "AS": "Asia",
    "EU": "Europe",
    "NA": "North America",
    "OC": "Oceania",
    "SA": "South America"
}


def create_continent(code, name):
    """
    Creates a continent object and saves it.
    :param code: code of the continent
    :param name: name of the continent
    :return: a continent object or None
    """
    if continent_exists(code):
        return None

    c = continent.Continent(code=code,
                            name=name)
    c.save()
    return c


def continent_exists(code):
    """
    Check if the continent already exists.
    :param code: code of the continent
    :return: true if the continent is already present in the database.
    """
    if continent.Continent.objects.filter(code=code).exists():
        return True
    return False


def add_continents():
    """
    Add the continent contained in the 'dic_code_continent'
    to the database.
    :return:
    """
    # k corresponds to the code and v to the continent's name.
    for (k, v) in dic_code_continent.items():
        create_continent(k, v)

##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
import datetime
import itertools
import string

import factory

from base.models.enums import entity_type, organization_type
from base.tests.factories.entity import EntityFactory


def generate_acronyms():
    acronyms_letters_generator = itertools.permutations(string.ascii_uppercase, r=4)
    for acronym_letters in acronyms_letters_generator:
        yield "".join(acronym_letters)


class EntityVersionFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'base.EntityVersion'

    entity = factory.SubFactory(EntityFactory)
    title = factory.Faker('company')
    acronym = factory.Iterator(generate_acronyms())
    entity_type = factory.Iterator(entity_type.ENTITY_TYPES, getter=lambda c: c[0])
    parent = factory.SubFactory(EntityFactory)
    start_date = datetime.date(2015, 1, 1).isoformat()
    end_date = None


class MainEntityVersionFactory(EntityVersionFactory):
    entity = factory.SubFactory(EntityFactory, organization__type=organization_type.MAIN)
    entity_type = factory.Iterator(entity_type.PEDAGOGICAL_ENTITY_TYPES)

##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from datetime import date

from base.models.enums.entity_type import SECTOR, FACULTY
from base.models.enums.organization_type import MAIN
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from reference.tests.factories.country import CountryFactory


def create_entities_hierarchy(organization_type=MAIN):
    country = CountryFactory()
    start_date = date.today().replace(year=1900)
    organization = OrganizationFactory(type=organization_type)
    root_entity = EntityFactory(country=country, organization=organization)
    root_entity_version = EntityVersionFactory(entity=root_entity,
                                               acronym="ROOT_V",
                                               entity_type=SECTOR,
                                               parent=None,
                                               end_date=None,
                                               start_date=start_date)

    child_one_entity = EntityFactory(country=country, organization=organization)
    child_one_entity_version = EntityVersionFactory(acronym="CHILD_1_V",
                                                    parent=root_entity,
                                                    entity_type=FACULTY,
                                                    end_date=None,
                                                    entity=child_one_entity,
                                                    start_date=start_date)

    child_two_entity = EntityFactory(country=country, organization=organization)
    child_two_entity_version = EntityVersionFactory(acronym="CHILD_2_V",
                                                    parent=root_entity,
                                                    entity_type=FACULTY,
                                                    end_date=None,
                                                    entity=child_two_entity,
                                                    start_date=start_date)

    return locals()

# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import random

from base.models import person
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY
from base.tests.factories.education_group_year import string_generator
from features.pages.education_group import pages


def fill_training_form(page: pages.NewTrainingPage, person_obj: person.Person) -> dict:
    management_entity = get_random_entity_version(person_obj)
    requirement_entity = management_entity
    title = string_generator()
    title_english = string_generator()

    page.entite_de_gestion = management_entity.acronym
    page.entite_dadministration = requirement_entity.acronym
    page.intitule_en_francais = title
    page.intitule_en_anglais = title_english
    return {
        "management_entity": management_entity,
        "requirement_entity": requirement_entity,
        "title_english": title_english,
        "title": title
    }


def fill_mini_training_form(page: pages.NewTrainingPage, person_obj: person.Person) -> dict:
    management_entity = get_random_entity_version(person_obj)
    title = string_generator()

    page.entite_de_gestion = management_entity.acronym
    page.intitule_en_francais = title
    return {
        "management_entity": management_entity,
        "title": title
    }


def get_random_entity_version(person_obj: person.Person) -> EntityVersion:
    ev = EntityVersion.objects.get(entity__personentity__person=person_obj)
    entities_version = [ev] + list(ev.descendants)
    faculties = [ev for ev in entities_version if ev.entity_type == FACULTY]
    random_entity_version = random.choice(faculties)
    return random_entity_version

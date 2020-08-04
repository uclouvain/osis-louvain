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
from base.models.campus import Campus
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY
from features.pages.learning_unit import pages


def fill_partim_form_for_faculty_manager(page: pages.NewPartimPage):
    form_data = {
        "partim_code": "C",
    }

    page.code_dedie_au_partim = form_data["partim_code"]
    return form_data


def fill_other_collective_form_for_central_manager(page: pages.NewLearningUnitPage, person_obj: person.Person):
    requirement_entity = random_entity(person_obj)
    form_data = {
        "code": "WMEDI1234",
        "type": "OTHER_COLLECTIVE",
        "credits": random.randint(1, 10),
        "intitule_commun": "Title",
        "intitule_commun_english": "Title english",
        "lieu_denseignement": random.choice(page.lieu_denseignement.options).text,
        "entite_resp_cahier_des_charges": requirement_entity.acronym,
        "entite_dattribution": requirement_entity.acronym
    }
    for field_name, field_value in form_data.items():
        setattr(page, field_name, field_value)
    return form_data


def random_entity(person_obj: person.Person):
    ev = EntityVersion.objects.get(entity__personentity__person=person_obj)
    entities_version = [ev] + list(ev.descendants)
    faculties = [ev for ev in entities_version if ev.entity_type == FACULTY]
    return random.choice(faculties)

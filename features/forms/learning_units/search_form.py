# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.models.entity_version import EntityVersion
from base.models.learning_unit_year import LearningUnitYear
from base.models.tutor import Tutor
from features.pages.learning_unit import pages


def fill_code(page: pages.SearchLearningUnitPage) -> dict:
    learning_unit_year_to_research = LearningUnitYear.objects.all().order_by("?").first()
    page.acronym = learning_unit_year_to_research.acronym
    return {"acronym": learning_unit_year_to_research.acronym}


def fill_container_type(page: pages.SearchLearningUnitPage) -> dict:
    container_type_to_search = random.choice(page.container_type.options).text
    page.container_type = container_type_to_search
    return {"container_type": container_type_to_search}


def fill_entity(page: pages.SearchLearningUnitPage) -> dict:
    entity_to_search = EntityVersion.objects.all().order_by("?").first()
    page.requirement_entity = entity_to_search.acronym
    return {"requirement_entity": entity_to_search.acronym}


def fill_tutor(page: pages.SearchLearningUnitPage) -> dict:
    tutor_to_search = Tutor.objects.all().order_by("?").first()
    page.tutor = tutor_to_search.person.full_name
    return {"tutor": tutor_to_search}

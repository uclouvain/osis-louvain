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
from base.models import proposal_learning_unit
from base.models.academic_year import current_academic_year
from base.models.entity_container_year import find_last_entity_version_grouped_by_linktypes, search
from base.models.utils.person_entity_filter import filter_by_attached_entities
from base.models.enums import entity_container_year_link_type, proposal_type, learning_unit_year_subtypes, \
    learning_container_year_types


def compute_form_initial_data(learning_unit_year):
    entities_version = find_last_entity_version_grouped_by_linktypes(learning_unit_year.learning_container_year)
    initial_data = {
        "academic_year": learning_unit_year.academic_year.id,
        "first_letter": learning_unit_year.acronym[0],
        "acronym": learning_unit_year.acronym[1:],
        "title": learning_unit_year.title,
        "title_english": learning_unit_year.title_english,
        "container_type": learning_unit_year.learning_container_year.container_type,
        "subtype": learning_unit_year.subtype,
        "internship_subtype": learning_unit_year.internship_subtype,
        "credits": learning_unit_year.credits,
        "periodicity": learning_unit_year.learning_unit.periodicity,
        "status": learning_unit_year.status,
        "language": learning_unit_year.learning_container_year.language,
        "quadrimester": learning_unit_year.quadrimester,
        "campus": learning_unit_year.learning_container_year.campus,
        "requirement_entity": entities_version.get(entity_container_year_link_type.REQUIREMENT_ENTITY),
        "allocation_entity": entities_version.get(entity_container_year_link_type.ALLOCATION_ENTITY),
        "additional_entity_1": entities_version.get(entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1),
        "additional_entity_2": entities_version.get(entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2)
    }
    return {key: value for key, value in initial_data.items() if value is not None}


def compute_proposal_type(initial_data, current_data):
    data_changed = _compute_data_changed(initial_data, current_data)
    filtered_data_changed = filter(lambda key: key not in ["academic_year", "subtype", "acronym"], data_changed)
    transformation = current_data["acronym"] != "{}{}".format(initial_data["first_letter"], initial_data["acronym"])
    modification = any(map(lambda x: x != "acronym", filtered_data_changed))
    if transformation and modification:
        return proposal_type.ProposalType.TRANSFORMATION_AND_MODIFICATION.name
    elif transformation:
        return proposal_type.ProposalType.TRANSFORMATION.name
    return proposal_type.ProposalType.MODIFICATION.name


def _compute_data_changed(initial_data, current_data):
    data_changed = []
    for key, value in initial_data.items():
        current_value = current_data.get(key)
        if str(value) != str(current_value):
            data_changed.append(key)
    return data_changed


def is_eligible_for_modification_proposal(learning_unit_year, a_person):
    proposal = proposal_learning_unit.find_by_learning_unit_year(learning_unit_year)
    current_year = current_academic_year().year
    entity_containers_year = search(learning_container_year=learning_unit_year.learning_container_year,
                                    link_type=entity_container_year_link_type.REQUIREMENT_ENTITY)

    if not filter_by_attached_entities(a_person, entity_containers_year).count():
        return False

    if learning_unit_year.academic_year.year < current_year:
        return False

    if learning_unit_year.learning_container_year.container_type not in (learning_container_year_types.COURSE,
                                                                         learning_container_year_types.DISSERTATION,
                                                                         learning_container_year_types.INTERNSHIP):
        return False

    if learning_unit_year.subtype == learning_unit_year_subtypes.PARTIM:
        return False

    if proposal:
        return False

    return True

##############################################################################
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
##############################################################################
from collections import OrderedDict

from django.db import models

from base.business import entity_version as business_entity_version
from base.models import entity_container_year, entity_component_year, learning_unit_year
from base.models.enums import entity_container_year_link_type as entity_types
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITIES
from base.models.learning_component_year import LearningComponentYear
from osis_common.utils.numbers import to_float_or_zero


def get_with_context(**learning_unit_year_data):
    entity_container_prefetch = models.Prefetch(
        'learning_container_year__entitycontaineryear_set',
        queryset=entity_container_year.search(
            link_type=REQUIREMENT_ENTITIES
        ).prefetch_related(
            models.Prefetch('entity__entityversion_set', to_attr='entity_versions')
        ),
        to_attr='entity_containers_year'
    )

    learning_unit_years = learning_unit_year.search(**learning_unit_year_data) \
        .select_related('academic_year', 'learning_container_year') \
        .prefetch_related(entity_container_prefetch) \
        .prefetch_related(get_learning_component_prefetch()) \
        .order_by('academic_year__year', 'acronym')

    learning_unit_years = [append_latest_entities(luy) for luy in learning_unit_years]
    learning_unit_years = [append_components(luy) for luy in learning_unit_years]

    return learning_unit_years


def append_latest_entities(learning_unit_yr, service_course_search=False):
    learning_unit_yr.entities = {}

    for entity_container_yr in learning_unit_yr.learning_container_year.entitycontaineryear_set.all():
        link_type = entity_container_yr.type
        learning_unit_yr.entities[link_type] = entity_container_yr.get_latest_entity_version()

    requirement_entity_version = learning_unit_yr.entities.get(entity_types.REQUIREMENT_ENTITY)
    allocation_entity_version = learning_unit_yr.entities.get(entity_types.ALLOCATION_ENTITY)

    if service_course_search:
        learning_unit_yr.entities[business_entity_version.SERVICE_COURSE] = is_service_course(
            learning_unit_yr.academic_year,
            requirement_entity_version,
            allocation_entity_version
        )

    return learning_unit_yr


def append_components(learning_unit_year):
    learning_unit_year.components = OrderedDict()
    if learning_unit_year.learning_components:
        for component in learning_unit_year.learning_components:
            entity_components_year = component.entity_components_year
            req_entities_volumes = _get_requirement_entities_volumes(entity_components_year)
            vol_req_entity = req_entities_volumes.get(entity_types.REQUIREMENT_ENTITY, 0) or 0
            vol_add_req_entity_1 = req_entities_volumes.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0) or 0
            vol_add_req_entity_2 = req_entities_volumes.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0) or 0
            volume_global = vol_req_entity + vol_add_req_entity_1 + vol_add_req_entity_2
            planned_classes = component.planned_classes or 0

            learning_unit_year.components[component] = {
                'VOLUME_TOTAL': to_float_or_zero(component.hourly_volume_total_annual),
                'VOLUME_Q1': to_float_or_zero(component.hourly_volume_partial_q1),
                'VOLUME_Q2': to_float_or_zero(component.hourly_volume_partial_q2),
                'PLANNED_CLASSES': planned_classes,
                'VOLUME_' + entity_types.REQUIREMENT_ENTITY: vol_req_entity,
                'VOLUME_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1: vol_add_req_entity_1,
                'VOLUME_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2: vol_add_req_entity_2,
                'VOLUME_TOTAL_REQUIREMENT_ENTITIES': volume_global,
                'REAL_CLASSES': component.real_classes  # Necessary for xls comparison with proposition
            }
    return learning_unit_year


def _get_requirement_entities_volumes(entity_components_year):
    return {
        entity_type: _get_floated_only_element_of_list(
            [
                ecy.repartition_volume for ecy in entity_components_year
                if ecy.entity_container_year.type == entity_type
            ], default=0
        )
        for entity_type in REQUIREMENT_ENTITIES
    }


def _get_floated_only_element_of_list(a_list, default=None):
    len_of_list = len(a_list)
    if not len_of_list:
        return default
    elif len_of_list == 1:
        return float(a_list[0]) if a_list[0] else 0.0
    raise ValueError("The provided list should contain 0 or 1 elements")


def volume_learning_component_year(learning_component_year, entity_components_year):
    requirement_vols = _get_requirement_entities_volumes(entity_components_year)
    return {
        'VOLUME_TOTAL': learning_component_year.hourly_volume_total_annual,
        'VOLUME_Q1': learning_component_year.hourly_volume_partial_q1,
        'VOLUME_Q2': learning_component_year.hourly_volume_partial_q2,
        'PLANNED_CLASSES': learning_component_year.planned_classes or 1,
        'VOLUME_REQUIREMENT_ENTITY': requirement_vols.get(entity_types.REQUIREMENT_ENTITY, 0),
        'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1': requirement_vols.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0),
        'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2': requirement_vols.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0),
        'VOLUME_GLOBAL': sum([requirement_vols.get(entity_types.REQUIREMENT_ENTITY, 0),
                              requirement_vols.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0),
                              requirement_vols.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0)])
    }


def is_service_course(academic_year, requirement_entity_version, allocation_entity_version):
    if not requirement_entity_version or not allocation_entity_version \
            or requirement_entity_version == allocation_entity_version:
        return False
    requirement_parent_faculty = requirement_entity_version.find_faculty_version(academic_year)
    if not requirement_parent_faculty:
        return False

    allocation_parent_faculty = allocation_entity_version.find_faculty_version(academic_year)
    if not allocation_parent_faculty:
        return False
    return requirement_parent_faculty != allocation_parent_faculty


def get_learning_component_prefetch():
    return models.Prefetch(
        'learningcomponentyear_set',
        queryset=LearningComponentYear.objects.all().order_by('type', 'acronym').prefetch_related(
            models.Prefetch('entitycomponentyear_set',
                            queryset=entity_component_year.EntityComponentYear.objects.all()
                            .select_related('entity_container_year'),
                            to_attr='entity_components_year'
                            )
        ),
        to_attr='learning_components'
    )


def volume_from_initial_learning_component_year(learning_component_year, entity_components_year):
    requirement_vols = _get_requirement_entities_volumes(entity_components_year)
    return {
        'VOLUME_TOTAL': learning_component_year['hourly_volume_total_annual'],
        'VOLUME_Q1': learning_component_year['hourly_volume_partial_q1'],
        'VOLUME_Q2': learning_component_year['hourly_volume_partial_q2'],
        'PLANNED_CLASSES': learning_component_year.get('planned_classes'),
        'VOLUME_REQUIREMENT_ENTITY': requirement_vols.get(entity_types.REQUIREMENT_ENTITY, 0),
        'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1': requirement_vols.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0),
        'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2': requirement_vols.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0),
        'VOLUME_GLOBAL': sum([requirement_vols.get(entity_types.REQUIREMENT_ENTITY, 0),
                              requirement_vols.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0),
                              requirement_vols.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0)])
    }

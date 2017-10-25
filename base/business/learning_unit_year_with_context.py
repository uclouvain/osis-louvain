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
from collections import OrderedDict
from decimal import Decimal

from django.db import models

from base import models as mdl
from base.business import entity_version as business_entity_version
from base.models import entity_container_year, entity_version
from base.models.enums import entity_container_year_link_type as entity_types
from django.utils.translation import ugettext_lazy as _

UNDEFINED_VALUE = ''
VOLUME_FOR_UNKNOWN_QUADRIMESTER = -1

TOTAL_VOLUME_KEY = 'VOLUME_TOTAL'
VOLUME_PARTIAL_KEY = 'VOLUME_Q1'
VOLUME_REMAINING_KEY = 'VOLUME_Q2'
PLANNED_CLASSES_KEY = 'PLANNED_CLASSES'
VOLUME_TOTAL_REQUIREMENT_ENTITIES_KEY = 'VOLUME_TOTAL_REQUIREMENT_ENTITIES'
VOLUME_QUARTER_KEY = 'VOLUME_QUARTER'


class LearningUnitYearWithContext:
    def __init__(self, **kwargs):
        self.learning_unit_year = kwargs.get('learning_unit_year')


def get_with_context(**learning_unit_year_data):
    entity_container_prefetch = models.Prefetch(
        'learning_container_year__entitycontaineryear_set',
        queryset=mdl.entity_container_year
        .search(
            link_type=[
                entity_types.REQUIREMENT_ENTITY,
                entity_types.ALLOCATION_ENTITY,
                entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1,
                entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2
            ]
        )
        .prefetch_related(
            models.Prefetch('entity__entityversion_set', to_attr='entity_versions')
        ),
        to_attr='entity_containers_year'
    )

    learning_component_prefetch = models.Prefetch(
        'learningunitcomponent_set',
        queryset=mdl.learning_unit_component.LearningUnitComponent.objects.all()
        .order_by('learning_component_year__type', 'learning_component_year__acronym')
        .select_related('learning_component_year')
        .prefetch_related(
            models.Prefetch('learning_component_year__entitycomponentyear_set',
                            queryset=mdl.entity_component_year.EntityComponentYear.objects.all()
                            .select_related('entity_container_year'),
                            to_attr='entity_components_year'
                            )
        ),
        to_attr='learning_unit_components'
    )

    learning_units = mdl.learning_unit_year.search(**learning_unit_year_data) \
        .select_related('academic_year', 'learning_container_year') \
        .prefetch_related(entity_container_prefetch) \
        .prefetch_related(learning_component_prefetch) \
        .order_by('academic_year__year', 'acronym')

    learning_units = [append_latest_entities(learning_unit) for learning_unit in learning_units]
    learning_units = [_append_components(learning_unit) for learning_unit in learning_units]

    return learning_units


def append_latest_entities(learning_unit, service_course_search=False):
    learning_unit.entities = {}
    learning_container_year = learning_unit.learning_container_year

    for entity_container_yr in getattr(learning_container_year, "entity_containers_year", []):
        link_type = entity_container_yr.type
        learning_unit.entities[link_type] = entity_container_yr.get_latest_entity_version()

    requirement_entity_version = learning_unit.entities.get(entity_types.REQUIREMENT_ENTITY)
    learning_unit_alloc_entity = learning_unit.entities.get(entity_types.ALLOCATION_ENTITY)

    if service_course_search and requirement_entity_version:
        entity_parent = requirement_entity_version.find_parent_faculty_version(learning_container_year.academic_year)
        if entity_parent:
            learning_unit.entities[business_entity_version.PARENT_FACULTY] = entity_parent
        else:
            learning_unit.entities[business_entity_version.PARENT_FACULTY] = requirement_entity_version

        if learning_unit_alloc_entity and requirement_entity_version != learning_unit_alloc_entity:
            learning_unit.entities[business_entity_version.SERVICE_COURSE] = is_service_course(learning_unit.academic_year,
                                                                        requirement_entity_version,
                                                                        learning_container_year, entity_parent)
        else:
            learning_unit.entities[business_entity_version.SERVICE_COURSE] = False

    return learning_unit


def _append_components(learning_unit):
    learning_unit.components = OrderedDict()
    if learning_unit.learning_unit_components:
        for learning_unit_component in learning_unit.learning_unit_components:
            component = learning_unit_component.learning_component_year
            entity_components_year = component.entity_components_year
            requirement_entities_volumes = _get_requirement_entities_volumes(entity_components_year)
            vol_req_entity = requirement_entities_volumes.get(entity_types.REQUIREMENT_ENTITY, 0) or 0
            vol_add_req_entity_1 = requirement_entities_volumes.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0) or 0
            vol_add_req_entity_2 = requirement_entities_volumes.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0) or 0
            volume_total_charge = vol_req_entity + vol_add_req_entity_1 + vol_add_req_entity_2
            volume_partial = float(component.hourly_volume_partial) if component.hourly_volume_partial else 0
            planned_classes = component.planned_classes or 1
            volume_total = volume_total_charge / planned_classes

            learning_unit.components[component] = {
                'VOLUME_TOTAL': volume_total,
                'VOLUME_Q1': volume_partial,
                'VOLUME_Q2': volume_total - volume_partial,
                'PLANNED_CLASSES': planned_classes,
                'VOLUME_' + entity_types.REQUIREMENT_ENTITY: vol_req_entity,
                'VOLUME_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1: vol_add_req_entity_1,
                'VOLUME_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2: vol_add_req_entity_2,
                'VOLUME_TOTAL_REQUIREMENT_ENTITIES': volume_total_charge,
            }
    return learning_unit


def _get_requirement_entities_volumes(entity_components_year):
    needed_entity_types = [
        entity_types.REQUIREMENT_ENTITY,
        entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1,
        entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2
    ]
    return {
        entity_type: _get_floated_only_element_of_list([ecy.hourly_volume_total for ecy in entity_components_year
                                                        if ecy.entity_container_year.type == entity_type], default=0)
        for entity_type in needed_entity_types
    }


def _get_floated_only_element_of_list(a_list, default=None):
    len_of_list = len(a_list)
    if not len_of_list:
        return default
    elif len_of_list == 1:
        return float(a_list[0]) if a_list[0] else 0.0
    raise ValueError("The provided list should contain 0 or 1 elements")


def volume_learning_component_year(learning_component_year, entity_components_year):
    requirement_entities_volumes = _get_requirement_entities_volumes(entity_components_year)
    vol_req_entity = requirement_entities_volumes.get(entity_types.REQUIREMENT_ENTITY, 0)
    vol_add_req_entity_1 = requirement_entities_volumes.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0)
    vol_add_req_entity_2 = requirement_entities_volumes.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0)
    volume_total_charge = vol_req_entity + vol_add_req_entity_1 + vol_add_req_entity_2
    volume_partial = learning_component_year.hourly_volume_partial
    planned_classes = learning_component_year.planned_classes or 1
    volume_total = Decimal(volume_total_charge / planned_classes)

    if volume_partial == VOLUME_FOR_UNKNOWN_QUADRIMESTER:
        volume_remaining = VOLUME_FOR_UNKNOWN_QUADRIMESTER
    elif volume_partial is None:
        volume_remaining = UNDEFINED_VALUE
        volume_partial = UNDEFINED_VALUE
    else:
        volume_remaining = volume_total - volume_partial

    return {
        TOTAL_VOLUME_KEY: volume_total,
        VOLUME_PARTIAL_KEY: volume_partial,
        VOLUME_REMAINING_KEY: volume_remaining,
        PLANNED_CLASSES_KEY: planned_classes,
        VOLUME_QUARTER_KEY: volume_distribution(volume_total, volume_partial)
    }


def volume_distribution(volume_total, volume_partial):
    component_partial_exists = False
    component_remaining_exists = False

    if volume_partial is None or volume_partial is UNDEFINED_VALUE:
        return UNDEFINED_VALUE
    else:
        if volume_partial == volume_total:
            component_partial_exists = True
        if volume_partial == 0.00:
            component_remaining_exists = True
        if volume_partial == VOLUME_FOR_UNKNOWN_QUADRIMESTER:
            return _('partial_or_remaining')
        if (volume_partial > 0.00) and (volume_partial < volume_total):
            return _('partial_remaining')

        if component_partial_exists:
            if component_remaining_exists:
                return _('partial_remaining')
            else:
                return _('partial')
        else:
            if component_remaining_exists:
                return _('remaining')

    return None


def is_service_course(academic_year, requirement_entity_version, learning_container_year, entity_parent):
    entity_container_yr_allocation = entity_container_year.find_allocation_entity(learning_container_year)
    if entity_container_yr_allocation == requirement_entity_version:
        return False

    elif entity_container_yr_allocation:
        entity_container_yr_requirement = entity_container_year.find_requirement_entity(learning_container_year)

        if not entity_parent and entity_container_yr_requirement:
            entity_parent = entity_container_yr_requirement.entity
        else:
            entity_parent = entity_parent.entity

        allocation_entity = entity_version.get_last_version(entity_container_yr_allocation.entity)
        requirement_entity = entity_version.get_last_version(entity_parent)
        if allocation_entity in requirement_entity.find_descendants(academic_year.start_date):
            return False

    return True
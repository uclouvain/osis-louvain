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
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.business import entity_version as business_entity_version
from base.models.enums import entity_container_year_link_type as entity_types

ENTITY_TYPES_VOLUME = [
    entity_types.REQUIREMENT_ENTITY,
    entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1,
    entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2
]


class LearningUnitYearWithContext:
    def __init__(self, **kwargs):
        self.learning_unit_year = kwargs.get('learning_unit_year')


def get_with_context(**learning_unit_year_data):
    entity_container_prefetch = models.Prefetch(
        'learning_container_year__entitycontaineryear_set',
        queryset=mdl.entity_container_year.search(
            link_type=ENTITY_TYPES_VOLUME
        ).prefetch_related(
            models.Prefetch('entity__entityversion_set', to_attr='entity_versions')
        ),
        to_attr='entity_containers_year'
    )

    learning_component_prefetch = models.Prefetch(
        'learningunitcomponent_set',
        queryset=mdl.learning_unit_component.LearningUnitComponent.objects.all().order_by(
            'learning_component_year__type', 'learning_component_year__acronym'
        ).select_related(
            'learning_component_year'
        ).prefetch_related(
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
    allocation_entity_version = learning_unit.entities.get(entity_types.ALLOCATION_ENTITY)

    if service_course_search:
        learning_unit.entities[business_entity_version.SERVICE_COURSE] = is_service_course(
            learning_unit.academic_year,
            requirement_entity_version,
            allocation_entity_version)

    return learning_unit


def _append_components(learning_unit):
    learning_unit.components = OrderedDict()
    if learning_unit.learning_unit_components:
        for learning_unit_component in learning_unit.learning_unit_components:
            component = learning_unit_component.learning_component_year
            entity_components_year = component.entity_components_year
            req_entities_volumes = _get_requirement_entities_volumes(entity_components_year)
            vol_req_entity = req_entities_volumes.get(entity_types.REQUIREMENT_ENTITY, 0) or 0
            vol_add_req_entity_1 = req_entities_volumes.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0) or 0
            vol_add_req_entity_2 = req_entities_volumes.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0) or 0
            volume_global = vol_req_entity + vol_add_req_entity_1 + vol_add_req_entity_2
            volume_partial_component = float(component.hourly_volume_partial) if component.hourly_volume_partial else 0
            planned_classes = component.planned_classes or 1
            volume_total = volume_global / planned_classes

            learning_unit.components[component] = {
                'VOLUME_TOTAL': volume_total,
                'VOLUME_Q1': volume_partial_component,
                'VOLUME_Q2': volume_total - volume_partial_component,
                'PLANNED_CLASSES': planned_classes,
                'VOLUME_' + entity_types.REQUIREMENT_ENTITY: vol_req_entity,
                'VOLUME_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1: vol_add_req_entity_1,
                'VOLUME_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2: vol_add_req_entity_2,
                'VOLUME_TOTAL_REQUIREMENT_ENTITIES': volume_global,
            }
    return learning_unit


def _get_requirement_entities_volumes(entity_components_year):
    needed_entity_types = [
        entity_types.REQUIREMENT_ENTITY,
        entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1,
        entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2
    ]
    return {
        entity_type: _get_floated_only_element_of_list([ecy.repartition_volume for ecy in entity_components_year
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
    volume_total = round(Decimal(volume_total_charge / planned_classes), 2)
    distribution = component_volume_distribution(volume_total, volume_partial)

    if distribution is None:
        volume_partial = None
        volume_remaining = None
    else:
        volume_remaining = volume_total - volume_partial

    return {
        'VOLUME_TOTAL': volume_total,
        'VOLUME_QUARTER': distribution,
        'VOLUME_Q1': volume_partial,
        'VOLUME_Q2': volume_remaining,
        'PLANNED_CLASSES': planned_classes,
        'VOLUME_REQUIREMENT_ENTITY': vol_req_entity,
        'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1': vol_add_req_entity_1,
        'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2': vol_add_req_entity_2
    }


def component_volume_distribution(volume_total, volume_partial):
    if volume_total is None or volume_total == 0.00 or volume_partial is None:
        return None
    elif volume_partial == volume_total:
        return _('partial')
    elif volume_partial == 0.00:
        return _('remaining')
    elif 0.00 < volume_partial < volume_total:
        return _('partial_remaining')
    else:
        return None


def is_service_course(academic_year, requirement_entity_version, allocation_entity_version):
    if not requirement_entity_version or not allocation_entity_version\
            or requirement_entity_version == allocation_entity_version:
        return False
    requirement_parent_faculty = requirement_entity_version.find_faculty_version(academic_year)
    if not requirement_parent_faculty:
        return False
    allocation_parent_faculty = allocation_entity_version.find_faculty_version(academic_year)
    if not allocation_parent_faculty:
        return False
    return requirement_parent_faculty != allocation_parent_faculty

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
from decimal import Decimal

from django.db import models
from django.db.models import Prefetch, Count

from base.business import entity_version as business_entity_version
from base.enums.component_detail import VOLUME_TOTAL, VOLUME_Q1, VOLUME_Q2, PLANNED_CLASSES, \
    VOLUME_REQUIREMENT_ENTITY, VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1, VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2, \
    VOLUME_TOTAL_REQUIREMENT_ENTITIES, REAL_CLASSES, VOLUME_GLOBAL
from base.models import learning_unit_year
from base.models.entity import Entity
from base.models.enums import entity_container_year_link_type as entity_types
from base.models.learning_component_year import LearningComponentYear


def get_with_context(**learning_unit_year_data):
    entity_version_prefetch = Entity.objects.all().prefetch_related(
        Prefetch('entityversion_set', to_attr='entity_versions')
    )
    requirement_entity_prefetch = models.Prefetch(
        'learning_container_year__requirement_entity',
        queryset=entity_version_prefetch
    )
    additional_entity_1_prefetch = models.Prefetch(
        'learning_container_year__additional_entity_1',
        queryset=entity_version_prefetch
    )
    additional_entity_2_prefetch = models.Prefetch(
        'learning_container_year__additional_entity_2',
        queryset=entity_version_prefetch
    )

    learning_unit_years = learning_unit_year.search(**learning_unit_year_data) \
        .select_related('academic_year', 'learning_container_year') \
        .prefetch_related(requirement_entity_prefetch) \
        .prefetch_related(additional_entity_1_prefetch) \
        .prefetch_related(additional_entity_2_prefetch) \
        .prefetch_related(get_learning_component_prefetch()) \
        .order_by('academic_year__year', 'acronym')

    learning_unit_years = [append_latest_entities(luy) for luy in learning_unit_years]
    learning_unit_years = [append_components(luy) for luy in learning_unit_years]

    return learning_unit_years


def append_latest_entities(learning_unit_yr, service_course_search=False):
    learning_unit_yr.entities = {}

    for link_type in entity_types.ENTITY_TYPE_LIST:
        container = learning_unit_yr.learning_container_year
        entity = container.get_entity_from_type(link_type)
        learning_unit_yr.entities[link_type] = entity.get_latest_entity_version() if entity else None

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
            req_entities_volumes = component.repartition_volumes
            vol_req_entity = req_entities_volumes.get(entity_types.REQUIREMENT_ENTITY, 0)
            vol_add_req_entity_1 = req_entities_volumes.get(
                entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0)
            vol_add_req_entity_2 = req_entities_volumes.get(
                entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0)
            volume_global = (vol_req_entity or Decimal(0)) + \
                            (vol_add_req_entity_1 or Decimal(0)) + \
                            (vol_add_req_entity_2 or Decimal(0))
            planned_classes = component.planned_classes or 0

            learning_unit_year.components[component] = {
                VOLUME_TOTAL: component.hourly_volume_total_annual,
                VOLUME_Q1: component.hourly_volume_partial_q1,
                VOLUME_Q2: component.hourly_volume_partial_q2,
                PLANNED_CLASSES: planned_classes,
                VOLUME_REQUIREMENT_ENTITY: vol_req_entity,
                VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1: vol_add_req_entity_1,
                VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2: vol_add_req_entity_2,
                VOLUME_TOTAL_REQUIREMENT_ENTITIES: volume_global,
                REAL_CLASSES: component.count_real_classes  # Necessary for xls comparison with proposition
            }
    return learning_unit_year


def volume_learning_component_year(learning_component_year):
    requirement_vols = learning_component_year.repartition_volumes
    planned_classes = learning_component_year.planned_classes or 1
    return {
        VOLUME_TOTAL: learning_component_year.hourly_volume_total_annual,
        VOLUME_Q1: learning_component_year.hourly_volume_partial_q1,
        VOLUME_Q2: learning_component_year.hourly_volume_partial_q2,
        PLANNED_CLASSES: planned_classes,
        VOLUME_REQUIREMENT_ENTITY: requirement_vols.get(entity_types.REQUIREMENT_ENTITY, 0),
        VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1: requirement_vols.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0),
        VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2: requirement_vols.get(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0),
        VOLUME_GLOBAL: learning_component_year.vol_global
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
        queryset=LearningComponentYear.objects.all().order_by(
            'type', 'acronym'
        ).annotate(count_real_classes=Count('learningclassyear')),
        to_attr='learning_components'
    )


def volume_from_initial_learning_component_year(learning_component_year, repartition_volumes):
    return {
        VOLUME_TOTAL: Decimal(learning_component_year['hourly_volume_total_annual'] or 0),
        VOLUME_Q1: Decimal(learning_component_year['hourly_volume_partial_q1'] or 0),
        VOLUME_Q2: Decimal(learning_component_year['hourly_volume_partial_q2'] or 0),
        PLANNED_CLASSES: learning_component_year.get('planned_classes'),
        VOLUME_REQUIREMENT_ENTITY: Decimal(repartition_volumes.get(VOLUME_REQUIREMENT_ENTITY, 0) or 0),
        VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1: Decimal(repartition_volumes.get(VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1,
                                                                                0) or 0),
        VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2: Decimal(repartition_volumes.get(VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2,
                                                                                0) or 0),
        VOLUME_GLOBAL: sum([Decimal(repartition_volumes.get(VOLUME_REQUIREMENT_ENTITY, 0) or 0),
                            Decimal(repartition_volumes.get(VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1, 0) or 0),
                            Decimal(repartition_volumes.get(VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2, 0) or 0)])
    }

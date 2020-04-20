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
from django.db.models import Prefetch

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_1, ADDITIONAL_REQUIREMENT_ENTITY_2


def get_entities_ids(entity_acronym, with_entity_subordinated):
    if entity_acronym:
        entity_versions = EntityVersion.objects.filter(acronym__iregex=entity_acronym)
        entities_ids = set(entity_versions.values_list('entity', flat=True))

        if with_entity_subordinated and entity_versions:
            # it is not possible to have the list of descendants
            # when the entity_version is empty
            list_descendants = EntityVersion.objects.get_tree(
                Entity.objects.filter(entityversion__acronym__iregex=entity_acronym)
            )
            entities_ids |= {row["entity_id"] for row in list_descendants}

        return list(entities_ids)
    return []


def build_entity_container_prefetch(entity_container_year_link_type):
    parent_version_prefetch = Prefetch(
        'parent__entityversion_set',
        to_attr='entity_versions'
    )
    entity_version_prefetch = Prefetch(
        'entityversion_set',
        queryset=EntityVersion.objects.prefetch_related(parent_version_prefetch),
        to_attr='entity_versions')
    prefetch_relation = {
        REQUIREMENT_ENTITY: 'learning_container_year__requirement_entity',
        ALLOCATION_ENTITY: 'learning_container_year__allocation_entity',
        ADDITIONAL_REQUIREMENT_ENTITY_1: 'learning_container_year__additional_entity_1',
        ADDITIONAL_REQUIREMENT_ENTITY_2: 'learning_container_year__additional_entity_2',
    }[entity_container_year_link_type]
    entity_container_prefetch = Prefetch(
        prefetch_relation,
        queryset=Entity.objects.all().prefetch_related(entity_version_prefetch)
    )
    return entity_container_prefetch

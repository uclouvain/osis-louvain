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
from django.db.models import Prefetch
from django.utils import timezone

from base import models as mdl
from base.models import entity_calendar, entity_version
from base.models import entity_version as mdl_entity_version
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums import academic_calendar_type


def get_entities_ids(entity_acronym, with_entity_subordinated):
    if entity_acronym:
        entity_versions = EntityVersion.objects.filter(acronym__iregex=entity_acronym)
        entities_ids = set(entity_versions.values_list('entity', flat=True))

        if with_entity_subordinated:
            list_descendants = EntityVersion.objects.get_tree(
                Entity.objects.filter(entityversion__acronym__iregex=entity_acronym)
            )
            entities_ids |= {row["entity_id"] for row in list_descendants}

        return list(entities_ids)
    return []


def get_entity_calendar(an_entity_version, academic_yr):
    entity_cal = entity_calendar.find_by_entity_and_reference(
        an_entity_version.entity.id,
        academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
        academic_yr
    )

    if entity_cal:
        return entity_cal
    else:
        if an_entity_version.parent:
            parent_entity_version = entity_version.find_latest_version_by_entity(an_entity_version.parent,
                                                                                 timezone.now())
            if parent_entity_version:
                return get_entity_calendar(parent_entity_version, academic_yr)
        return None


def build_entity_container_prefetch(entity_container_year_link_types):
    parent_version_prefetch = Prefetch('parent__entityversion_set',
                                       queryset=mdl_entity_version.search(),
                                       to_attr='entity_versions')
    entity_version_prefetch = Prefetch('entity__entityversion_set',
                                       queryset=mdl_entity_version.search()
                                       .prefetch_related(parent_version_prefetch),
                                       to_attr='entity_versions')
    entity_container_prefetch = Prefetch('learning_container_year__entitycontaineryear_set',
                                         queryset=mdl.entity_container_year.search(
                                             link_type=entity_container_year_link_types)
                                         .prefetch_related(entity_version_prefetch),
                                         to_attr='entity_containers_year')
    return entity_container_prefetch

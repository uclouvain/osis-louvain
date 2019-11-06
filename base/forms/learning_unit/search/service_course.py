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
from base.business.entity import build_entity_container_prefetch
from base.business.entity_version import SERVICE_COURSE
from base.business.learning_unit_year_with_context import append_latest_entities
from base.forms.learning_unit.search.simple import LearningUnitFilter
from base.models.enums import entity_container_year_link_type


class ServiceCourseFilter(LearningUnitFilter):

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        qs = qs.prefetch_related(
            build_entity_container_prefetch(entity_container_year_link_type.ALLOCATION_ENTITY),
            build_entity_container_prefetch(entity_container_year_link_type.REQUIREMENT_ENTITY),
        )

        for luy in qs:
            append_latest_entities(luy, service_course_search=True)

        return qs.filter(pk__in=[lu.pk for lu in qs if lu.entities.get(SERVICE_COURSE)])

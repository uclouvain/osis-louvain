##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import functools
import operator
from typing import Optional, List

from django.db.models import F, QuerySet, OuterRef, Subquery, Q

from base.models.enums import learning_container_year_types, learning_component_year_type
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_year import LearningUnitYear, LearningUnitYearQuerySet
from ddd.logic.application.domain.builder.vacant_course_builder import VacantCourseBuilder
from ddd.logic.application.domain.model.vacant_course import VacantCourseIdentity, VacantCourse
from ddd.logic.application.dtos import VacantCourseFromRepositoryDTO
from ddd.logic.application.repository.i_vacant_course_repository import IVacantCourseRepository


class VacantCourseRepository(IVacantCourseRepository):
    @classmethod
    def search(cls, entity_ids: Optional[List[VacantCourseIdentity]] = None, **kwargs) -> List[VacantCourse]:
        qs = _vacant_course_base_qs()

        if entity_ids is not None:
            filter_clause = functools.reduce(
                operator.or_,
                ((Q(code=entity_id.code) & Q(year=entity_id.year)) for entity_id in entity_ids)
            )
            qs = qs.filter(filter_clause)

        results = []
        for row_as_dict in qs:
            dto_from_database = VacantCourseFromRepositoryDTO(**row_as_dict)
            results.append(VacantCourseBuilder.build_from_repository_dto(dto_from_database))
        return results

    @classmethod
    def get(cls, entity_id: 'VacantCourseIdentity') -> 'VacantCourse':
        qs = _vacant_course_base_qs().filter(
            code=entity_id.code,
            year=entity_id.year,
        )
        obj_as_dict = qs.get()
        dto_from_database = VacantCourseFromRepositoryDTO(**obj_as_dict)
        return VacantCourseBuilder.build_from_repository_dto(dto_from_database)


def _vacant_course_base_qs() -> QuerySet:
    subqs = LearningComponentYear.objects.filter(learning_unit_year_id=OuterRef('pk'))

    main_qs = LearningUnitYearQuerySet.annotate_entity_allocation_acronym(
        LearningUnitYear.objects.filter(
            learning_container_year__container_type__in=[
                learning_container_year_types.COURSE,
                learning_container_year_types.INTERNSHIP,
                learning_container_year_types.DISSERTATION
            ]
        ).annotate_full_title()
    )

    return main_qs.annotate(
            code=F('learning_container_year__acronym'),
            year=F('learning_container_year__academic_year__year'),
            title=F('full_title'),
            is_in_team=F('learning_container_year__team'),
            vacant_declaration_type=F('learning_container_year__type_declaration_vacant'),
            lecturing_volume_available=Subquery(
                subqs.filter(type=learning_component_year_type.LECTURING).values('volume_declared_vacant')[:1]
            ),
            practical_volume_available=Subquery(
                subqs.filter(type=learning_component_year_type.PRACTICAL_EXERCISES).values('volume_declared_vacant')[:1]
            )
        ).values(
            "code",
            "year",
            "title",
            "is_in_team",
            "vacant_declaration_type",
            "lecturing_volume_available",
            "practical_volume_available",
            "entity_allocation"
        )

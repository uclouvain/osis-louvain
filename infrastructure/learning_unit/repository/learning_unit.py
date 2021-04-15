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
from typing import Optional, List

from django.db.models import F, OuterRef, Subquery, Case, When, Q, CharField, Value
from django.db.models.functions import Concat

from base.models.academic_year import AcademicYear as AcademicYearDatabase
from base.models.entity_version import EntityVersion as EntityVersionDatabase
from base.models.learning_container import LearningContainer as LearningContainerDatabase
from base.models.learning_container_year import LearningContainerYear as LearningContainerYearDatabase
from base.models.learning_unit import LearningUnit as LearningUnitDatabase
from base.models.learning_unit_year import LearningUnitYear as LearningUnitYearDatabase
from ddd.logic.learning_unit.builder.learning_unit_builder import LearningUnitBuilder
from ddd.logic.learning_unit.domain.model.learning_unit import LearningUnit, LearningUnitIdentity
from ddd.logic.learning_unit.dtos import LearningUnitFromRepositoryDTO, LearningUnitSearchDTO
from ddd.logic.learning_unit.repository.i_learning_unit import ILearningUnitRepository
from ddd.logic.shared_kernel.academic_year.builder.academic_year_identity_builder import AcademicYearIdentityBuilder
from osis_common.ddd.interface import EntityIdentity, ApplicationService, Entity
from reference.models.language import Language as LanguageDatabase


class LearningUnitRepository(ILearningUnitRepository):

    @classmethod
    def search_learning_units_dto(
            cls,
            code: str = None,
            year: int = None,
            full_title: str = None,
            type: str = None,
            responsible_entity_code: str = None
    ) -> List['LearningUnitSearchDTO']:
        qs = _get_common_queryset()
        # FIXME :: reuse Django filter
        if code is not None:
            qs = qs.filter(
                acronym__icontains=code,
            )
        if year is not None:
            qs = qs.filter(
                academic_year__year=year,
            )
        if type is not None:
            qs = qs.filter(
                learning_container_year__container_type=type,
            )
        if responsible_entity_code is not None:
            qs = qs.filter(
                requirement_entity__entityversion__acronym__icontains=responsible_entity_code,
            )
        if full_title is not None:
            qs = qs.filter(
                Q(learning_container_year__common_title__icontains=full_title)
                | Q(specific_title__icontains=full_title),
            )

        qs = qs.annotate(
            code=F('acronym'),
            year=F('academic_year__year'),
            type=F('learning_container_year__container_type'),
            full_title=Case(
                When(
                    Q(learning_container_year__common_title__isnull=True) |
                    Q(learning_container_year__common_title__exact=''),
                    then='specific_title'
                ),
                When(
                    Q(specific_title__isnull=True) | Q(specific_title__exact=''),
                    then='learning_container_year__common_title'
                ),
                default=Concat('learning_container_year__common_title', Value(' - '), 'specific_title'),
                output_field=CharField(),
            ),
            responsible_entity_code=Subquery(
                EntityVersionDatabase.objects.filter(
                    entity__id=OuterRef('requirement_entity_id')
                ).order_by('-start_date').values('acronym')[:1]
            ),
            responsible_entity_title=Subquery(
                EntityVersionDatabase.objects.filter(
                    entity__id=OuterRef('requirement_entity_id')
                ).order_by('-start_date').values('title')[:1]
            ),
        ).values(
            "year",
            "code",
            "full_title",
            "type",
            "responsible_entity_code",
            "responsible_entity_title",
        )
        result = []
        for data_dict in qs.values():
            result.append(LearningUnitSearchDTO(**data_dict))
        return result

    @classmethod
    def save(cls, entity: 'LearningUnit') -> None:
        # FIXME :: use get_or_create (or save) instead of Django create()
        learning_container = LearningContainerDatabase.objects.create()

        learning_unit = LearningUnitDatabase.objects.create(
            learning_container=learning_container,
        )

        requirement_entity_id = EntityVersionDatabase.objects.filter(
            acronym=entity.responsible_entity_identity.code
        ).values_list('entity_id', flat=True).get()

        academic_year_id = AcademicYearDatabase.objects.filter(
            year=entity.academic_year.year
        ).values_list('pk', flat=True).get()

        learning_container_year = LearningContainerYearDatabase.objects.create(
            acronym=entity.code,
            academic_year_id=academic_year_id,
            container_type=entity.type.name,
            common_title=entity.titles.common_fr,
            common_title_english=entity.titles.common_en,
            requirement_entity_id=requirement_entity_id
        )

        language_id = LanguageDatabase.objects.filter(
            code=entity.language.iso_code
        ).values_list('pk', flat=True).get()

        learn_unit_year = LearningUnitYearDatabase.objects.create(
            learning_unit=learning_unit,
            academic_year_id=academic_year_id,
            learning_container_year=learning_container_year,
            acronym=entity.code,  # FIXME :: Is this correct ? Duplicated with container.acronym ?
            specific_title=entity.titles.specific_fr,
            specific_title_english=entity.titles.specific_en,
            credits=entity.titles.credits,
            internship_subtype=entity.internship_subtype.name,
            periodicity=entity.periodicity.name,
            language_id=language_id,
            faculty_remark=entity.remarks.faculty,
            other_remark=entity.remarks.publication_fr,
            other_remark_english=entity.remarks.publication_en,
        )

        return entity.entity_id

    @classmethod
    def get(cls, entity_id: 'LearningUnitIdentity') -> 'LearningUnit':
        qs = _get_common_queryset().filter(acronym=entity_id.code, academic_year__year=entity_id.year)
        qs = _annotate_queryset(qs)
        qs = _values_queryset(qs)
        obj_as_dict = qs.get()
        dto_from_database = LearningUnitFromRepositoryDTO(**obj_as_dict)
        return LearningUnitBuilder.build_from_repository_dto(dto_from_database)

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[Entity]:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'LearningUnitIdentity', **kwargs: 'ApplicationService') -> None:
        obj = LearningUnitYearDatabase.objects.get(
            acronym=entity_id.code,
            academic_year__year=entity_id.year,
        )
        obj.delete()

    def get_identities(self) -> List['LearningUnitIdentity']:
        all_learn_unit_years = LearningUnitYearDatabase.objects.all().values(
            "acronym",
            "academic_year__year",
        )

        return [
            LearningUnitIdentity(
                code=learning_unit['acronym'],
                academic_year=AcademicYearIdentityBuilder.build_from_year(year=learning_unit['academic_year__year'])
            )
            for learning_unit in all_learn_unit_years
        ]


def _annotate_queryset(queryset):
    queryset = queryset.annotate(
        code=F('acronym'),
        year=F('academic_year__year'),
        type=F('learning_container_year__container_type'),
        common_title_fr=F('learning_container_year__common_title'),
        specific_title_fr=F('specific_title'),
        common_title_en=F('learning_container_year__common_title_english'),
        specific_title_en=F('specific_title_english'),
        responsible_entity_code=Subquery(
            EntityVersionDatabase.objects.filter(
                entity__id=OuterRef('requirement_entity_id')
            ).order_by('-start_date').values('acronym')[:1]
        ),
        iso_code=F('language__code'),
        remark_faculty=F('faculty_remark'),
        remark_publication_fr=F('other_remark'),
        remark_publication_en=F('other_remark_english'),
    )
    return queryset


def _values_queryset(queryset):
    queryset = queryset.values(
        'code',
        'year',
        'type',
        'common_title_fr',
        'specific_title_fr',
        'common_title_en',
        'specific_title_en',
        'credits',
        'internship_subtype',
        'responsible_entity_code',
        'periodicity',
        'iso_code',
        'remark_faculty',
        'remark_publication_fr',
        'remark_publication_en',
    )
    return queryset


def _get_common_queryset():
    return LearningUnitYearDatabase.objects.all()

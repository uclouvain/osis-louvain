##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.db import IntegrityError
from django.db.models import Prefetch, Subquery, OuterRef, Q
from django.utils import timezone

from education_group.ddd.business_types import *

from base.models.academic_year import AcademicYear as AcademicYearModelDb
from base.models.education_group_type import EducationGroupType as EducationGroupTypeModelDb
from base.models.entity import Entity as EntityModelDb
from base.models.entity_version import EntityVersion as EntityVersionModelDb
from base.models.campus import Campus as CampusModelDb
from education_group.ddd.domain.service.enum_converter import EducationGroupTypeConverter
from education_group.models.group_year import GroupYear as GroupYearModelDb
from education_group.models.group import Group as GroupModelDb
from base.models.enums.constraint_type import ConstraintTypeEnum
from education_group.ddd.domain import exception, group
from education_group.ddd.domain.group import GroupIdentity
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain._remark import Remark
from education_group.ddd.domain._titles import Titles
from education_group.ddd.domain._entity import Entity as EntityValueObject
from education_group.ddd.domain.exception import AcademicYearNotFound, TypeNotFound, ManagementEntityNotFound, \
    TeachingCampusNotFound
from osis_common.ddd import interface


class GroupRepository(interface.AbstractRepository):
    @classmethod
    def create(cls, group: 'Group', **_) -> 'GroupIdentity':
        try:
            academic_year = AcademicYearModelDb.objects.only('id').get(year=group.year)
            start_year = AcademicYearModelDb.objects.only('id').get(year=group.start_year)
            education_group_type = EducationGroupTypeModelDb.objects.only('id').get(name=group.type.name)
            management_entity = EntityVersionModelDb.objects.current(timezone.now()).only('entity_id').get(
                acronym=group.management_entity.acronym,
            )
            teaching_campus = CampusModelDb.objects.only('id').get(
                name=group.teaching_campus.name,
                organization__name=group.teaching_campus.university_name
            )

            end_year = None
            if group.end_year is not None:
                end_year = AcademicYearModelDb.objects.only('id').get(year=group.end_year)
        except AcademicYearModelDb.DoesNotExist:
            raise AcademicYearNotFound
        except EducationGroupTypeModelDb.DoesNotExist:
            raise TypeNotFound
        except EntityVersionModelDb.DoesNotExist:
            raise ManagementEntityNotFound
        except CampusModelDb.DoesNotExist:
            raise TeachingCampusNotFound

        group_qs = GroupModelDb.objects.filter(
            groupyear__partial_acronym=group.code
        ).order_by('groupyear__academic_year__year')
        group_pk = group_qs.only('pk').last().pk if group_qs else None

        group_upserted, created = GroupModelDb.objects.update_or_create(
            pk=group_pk,
            defaults={'start_year': start_year, 'end_year': end_year}
        )
        try:
            group_year_created = GroupYearModelDb.objects.create(
                partial_acronym=group.code,
                academic_year=academic_year,
                education_group_type=education_group_type,
                acronym=group.abbreviated_title,
                title_fr=group.titles.title_fr,
                title_en=group.titles.title_en,
                credits=group.credits,
                constraint_type=group.content_constraint.type.name if group.content_constraint.type else None,
                min_constraint=group.content_constraint.minimum,
                max_constraint=group.content_constraint.maximum,
                management_entity_id=management_entity.entity_id,
                main_teaching_campus=teaching_campus,
                group=group_upserted,
                remark_fr=group.remark.text_fr,
                remark_en=group.remark.text_en,
            )
        except IntegrityError:
            raise exception.GroupCodeAlreadyExistException

        return GroupIdentity(
            code=group_year_created.partial_acronym,
            year=group_year_created.academic_year.year
        )

    @classmethod
    def update(cls, group: 'Group', **_) -> 'GroupIdentity':
        try:
            management_entity = EntityVersionModelDb.objects.current(timezone.now()).only('entity_id').get(
                acronym=group.management_entity.acronym,
            )
            teaching_campus = CampusModelDb.objects.only('id').get(
                name=group.teaching_campus.name,
                organization__name=group.teaching_campus.university_name
            )
        except EntityVersionModelDb.DoesNotExist:
            raise ManagementEntityNotFound
        except CampusModelDb.DoesNotExist:
            raise TeachingCampusNotFound

        try:
            group_db_obj = GroupYearModelDb.objects.get(
                partial_acronym=group.entity_id.code,
                academic_year__year=group.entity_id.year
            )
        except GroupYearModelDb.DoesNotExist:
            raise exception.GroupNotFoundException

        group_db_obj.acronym = group.abbreviated_title
        group_db_obj.title_fr = group.titles.title_fr
        group_db_obj.title_en = group.titles.title_en
        group_db_obj.credits = group.credits
        group_db_obj.constraint_type = group.content_constraint.type.name if group.content_constraint.type else None
        group_db_obj.min_constraint = group.content_constraint.minimum
        group_db_obj.max_constraint = group.content_constraint.maximum
        group_db_obj.management_entity_id = management_entity.entity_id
        group_db_obj.main_teaching_campus = teaching_campus
        group_db_obj.remark_fr = group.remark.text_fr
        group_db_obj.remark_en = group.remark.text_en
        group_db_obj.save()
        return group.entity_id

    @classmethod
    def get(cls, entity_id: 'GroupIdentity') -> 'Group':
        results = cls.search([entity_id])
        if not results:
            raise exception.GroupNotFoundException
        return results[0]

    @classmethod
    def search(cls, entity_ids: Optional[List['GroupIdentity']] = None, **kwargs) -> List['Group']:
        if entity_ids:
            qs = GroupYearModelDb.objects.all().select_related(
                'academic_year',
                'education_group_type',
                'main_teaching_campus__organization',
                'group__start_year',
                'group__end_year',
            ).prefetch_related(
                Prefetch(
                    'management_entity',
                    EntityModelDb.objects.all().annotate(
                        most_recent_acronym=Subquery(
                            EntityVersionModelDb.objects.filter(
                                entity__id=OuterRef('pk')
                            ).order_by('-start_date').values('acronym')[:1]
                        )
                    )
                ),
            )
            filter_or_clause = Q()
            for entity_id in entity_ids:
                filter_or_clause |= Q(
                    partial_acronym=entity_id.code,
                    academic_year__year=entity_id.year
                )
            return [_convert_db_model_to_ddd_model(obj) for obj in qs.filter(filter_or_clause)]
        return []

    @classmethod
    def delete(cls, entity_id: 'GroupIdentity', **_) -> None:
        GroupYearModelDb.objects.filter(
            partial_acronym=entity_id.code,
            academic_year__year=entity_id.year
        ).delete()


def _convert_db_model_to_ddd_model(obj: GroupYearModelDb) -> 'Group':
    entity_id = GroupIdentity(code=obj.partial_acronym, year=obj.academic_year.year)
    return group.Group(
        entity_identity=entity_id,
        type=EducationGroupTypeConverter.convert_type_str_to_enum(obj.education_group_type.name),
        abbreviated_title=obj.acronym,
        titles=Titles(
            title_fr=obj.title_fr,
            title_en=obj.title_en,
        ),
        credits=obj.credits,
        content_constraint=ContentConstraint(
            type=ConstraintTypeEnum[obj.constraint_type] if obj.constraint_type else None,
            minimum=obj.min_constraint,
            maximum=obj.max_constraint,
        ),
        management_entity=EntityValueObject(
            acronym=obj.management_entity.most_recent_acronym,
        ),
        teaching_campus=Campus(
            name=obj.main_teaching_campus.name,
            university_name=obj.main_teaching_campus.organization.name,
        ),
        remark=Remark(
            text_fr=obj.remark_fr,
            text_en=obj.remark_en
        ),
        start_year=obj.group.start_year.year,
        end_year=obj.group.end_year.year if obj.group.end_year else None,
    )

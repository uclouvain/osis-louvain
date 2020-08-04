# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from typing import Optional, List

from django.db import IntegrityError
from django.db.models import Prefetch, Subquery, OuterRef
from django.utils import timezone

from base.models.academic_year import AcademicYear as AcademicYearModelDb
from base.models.campus import Campus as CampusModelDb
from base.models.education_group import EducationGroup as EducationGroupModelDb
from base.models.education_group_type import EducationGroupType as EducationGroupTypeModelDb
from base.models.education_group_year import EducationGroupYear as EducationGroupYearModelDb
from base.models.entity import Entity as EntityModelDb
from base.models.entity_version import EntityVersion as EntityVersionModelDb
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import MiniTrainingType
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd.domain import mini_training, exception
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain._entity import Entity as EntityValueObject
from education_group.ddd.domain._remark import Remark
from education_group.ddd.domain._titles import Titles
from osis_common.ddd import interface
from osis_common.ddd.interface import Entity, EntityIdentity


class MiniTrainingRepository(interface.AbstractRepository):
    @classmethod
    def create(cls, mini_training_obj: mini_training.MiniTraining, **_) -> mini_training.MiniTrainingIdentity:
        try:
            academic_year = AcademicYearModelDb.objects.get(year=mini_training_obj.year)
            start_year = AcademicYearModelDb.objects.get(year=mini_training_obj.start_year)
            end_year = AcademicYearModelDb.objects.get(year=mini_training_obj.end_year) \
                if mini_training_obj.end_year else None
            education_group_type = EducationGroupTypeModelDb.objects.only('id').get(name=mini_training_obj.type.name)
            management_entity = EntityVersionModelDb.objects.current(timezone.now()).only('entity_id').get(
                acronym=mini_training_obj.management_entity.acronym,
            )
            teaching_campus = CampusModelDb.objects.only('id').get(
                name=mini_training_obj.teaching_campus.name,
                organization__name=mini_training_obj.teaching_campus.university_name
            )
        except AcademicYearModelDb.DoesNotExist:
            raise exception.AcademicYearNotFound
        except EducationGroupTypeModelDb.DoesNotExist:
            raise exception.TypeNotFound
        except EntityVersionModelDb.DoesNotExist:
            raise exception.ManagementEntityNotFound
        except CampusModelDb.DoesNotExist:
            raise exception.TeachingCampusNotFound

        try:
            try:
                education_group_db_obj = EducationGroupModelDb.objects.filter(
                    educationgroupyear__acronym=mini_training_obj.acronym
                ).distinct().get()
            except EducationGroupModelDb.DoesNotExist:
                education_group_db_obj = EducationGroupModelDb.objects.create(
                    start_year=start_year,
                    end_year=end_year
                )

            education_group_year_db_obj = EducationGroupYearModelDb.objects.create(
                education_group=education_group_db_obj,
                academic_year=academic_year,
                partial_acronym=mini_training_obj.code,
                education_group_type=education_group_type,
                acronym=mini_training_obj.acronym,
                title=mini_training_obj.titles.title_fr,
                title_english=mini_training_obj.titles.title_en,
                credits=mini_training_obj.credits,
                management_entity_id=management_entity.entity_id,
                main_teaching_campus=teaching_campus,
                schedule_type=mini_training_obj.schedule_type.name,
                active=mini_training_obj.status.name,
                keywords=mini_training_obj.keywords
            )

        except IntegrityError:
            raise exception.MiniTrainingCodeAlreadyExistException()

        return mini_training_obj.entity_id

    @classmethod
    def update(cls, entity: Entity) -> EntityIdentity:
        pass

    @classmethod
    def get(cls, entity_id: mini_training.MiniTrainingIdentity) -> mini_training.MiniTraining:
        try:
            education_group_year_db = EducationGroupYearModelDb.objects.filter(
                acronym=entity_id.acronym,
                academic_year__year=entity_id.year
            ).select_related(
                "education_group",
                "academic_year",
                "education_group__start_year",
                "education_group__end_year",
                "education_group_type",
                "main_teaching_campus__organization"
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
            ).get()
        except EducationGroupYearModelDb.DoesNotExist:
            raise exception.MiniTrainingNotFoundException

        return mini_training.MiniTraining(
            entity_id=entity_id,
            entity_identity=entity_id,
            code=education_group_year_db.partial_acronym,
            type=_convert_type(education_group_year_db.education_group_type),
            abbreviated_title=education_group_year_db.acronym,
            titles=Titles(
                title_fr=education_group_year_db.title,
                title_en=education_group_year_db.title_english,
            ),
            status=ActiveStatusEnum[education_group_year_db.active] if education_group_year_db.active else None,
            schedule_type=ScheduleTypeEnum[education_group_year_db.schedule_type]
            if education_group_year_db.schedule_type else None,
            credits=education_group_year_db.credits,
            management_entity=EntityValueObject(
                acronym=education_group_year_db.management_entity.most_recent_acronym,
            ),
            teaching_campus=Campus(
                name=education_group_year_db.main_teaching_campus.name,
                university_name=education_group_year_db.main_teaching_campus.organization.name,
            ),
            start_year=education_group_year_db.education_group.start_year.year,
            end_year=education_group_year_db.education_group.end_year.year
            if education_group_year_db.education_group.end_year else None
        )

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[Entity]:
        pass

    @classmethod
    def delete(cls, entity_id: EntityIdentity) -> None:
        pass


def _convert_type(education_group_type):
    if education_group_type.name in MiniTrainingType.get_names():
        return MiniTrainingType[education_group_type.name]
    raise Exception('Unsupported group type')

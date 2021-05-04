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
from typing import List, Optional

from django.db.models import F, Q

from attribution.models.tutor_application import TutorApplication
from base.auth.roles.tutor import Tutor
from base.models.learning_container_year import LearningContainerYear
from ddd.logic.application.domain.builder.application_builder import ApplicationBuilder
from ddd.logic.application.domain.model.applicant import ApplicantIdentity
from ddd.logic.application.domain.model.application import ApplicationIdentity, Application
from ddd.logic.application.dtos import ApplicationFromRepositoryDTO
from ddd.logic.application.repository.i_application_repository import IApplicationRepository
from osis_common.ddd.interface import ApplicationService


class ApplicationRepository(IApplicationRepository):
    @classmethod
    def search(
            cls,
            entity_ids: Optional[List[ApplicationIdentity]] = None,
            applicant_id: Optional[ApplicantIdentity] = None, **kwargs
    ) -> List[Application]:
        qs = _application_base_qs()

        if entity_ids is not None:
            filter_clause = functools.reduce(
                operator.or_,
                ((Q(uuid=entity_id.uuid)) for entity_id in entity_ids)
            )
            qs = qs.filter(filter_clause)
        if applicant_id is not None:
            qs = qs.filter(tutor__person__global_id=applicant_id.global_id)

        results = []
        for row_as_dict in qs:
            dto_from_database = ApplicationFromRepositoryDTO(**row_as_dict)
            results.append(ApplicationBuilder.build_from_repository_dto(dto_from_database))
        return results

    @classmethod
    def get(cls, entity_id: 'ApplicationIdentity') -> 'Application':
        qs = _application_base_qs().filter(uuid=entity_id.uuid)

        obj_as_dict = qs.get()
        dto_from_database = ApplicationFromRepositoryDTO(**obj_as_dict)
        return ApplicationBuilder.build_from_repository_dto(dto_from_database)

    @classmethod
    def save(cls, application: Application) -> None:
        tutor_id = Tutor.objects.get(global_id=application.applicant_id.global_id).pk
        learning_container_year_id = LearningContainerYear.objects.get(
            acronym=application.course_id.code,
            academic_year__year=application.course_id.year
        ).pk

        obj, created = TutorApplication.objects.update_or_create(
            uuid=application.entity_id.uuid,
            defaults={
                "tutor_id": tutor_id,
                "learning_container_year_id": learning_container_year_id,
                "volume_lecturing": application.lecturing_volume,
                "volume_pratical_exercice": application.practical_volume,
                "remark": application.remark,
                "course_summary": application.course_summary
            }
        )

    @classmethod
    def delete(cls, entity_id: ApplicationIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError


def _application_base_qs():
    return TutorApplication.objects.annotate(
        applicant_global_id=F('tutor__person__global_id'),
        vacant_course_code=F('learning_container_year__acronym'),
        vacant_course_year=F('learning_container_year__academic_year__year'),
        lecturing_volume=F('volume_lecturing'),
        practical_volume=F('volume_pratical_exercice')
    ).values(
        'uuid',
        'applicant_global_id',
        'vacant_course_code',
        'vacant_course_year',
        'lecturing_volume',
        'practical_volume',
        'remark',
        'course_summary'
    )

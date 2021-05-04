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

from django.db.models import F, QuerySet, Q

from base.auth.roles.tutor import Tutor
from ddd.logic.application.domain.builder.applicant_builder import ApplicantBuilder
from ddd.logic.application.domain.model.applicant import ApplicantIdentity, Applicant
from ddd.logic.application.dtos import ApplicantFromRepositoryDTO
from ddd.logic.application.repository.i_applicant_respository import IApplicantRepository


class ApplicantRepository(IApplicantRepository):
    @classmethod
    def search(cls, entity_ids: Optional[List[ApplicantIdentity]] = None, **kwargs) -> List[Applicant]:
        qs = _applicant_base_qs()

        if entity_ids is not None:
            filter_clause = functools.reduce(
                operator.or_,
                ((Q(global_id=entity_id.global_id)) for entity_id in entity_ids)
            )
            qs = qs.filter(filter_clause)

        results = []
        for row_as_dict in qs:
            dto_from_database = ApplicantFromRepositoryDTO(**row_as_dict)
            results.append(ApplicantBuilder.build_from_repository_dto(dto_from_database))
        return results

    @classmethod
    def get(cls, entity_id: 'ApplicantIdentity') -> 'Applicant':
        qs = _applicant_base_qs().filter(
            global_id=entity_id.global_id
        )

        obj_as_dict = qs.get()
        dto_from_database = ApplicantFromRepositoryDTO(**obj_as_dict)
        return ApplicantBuilder.build_from_repository_dto(dto_from_database)


def _applicant_base_qs() -> QuerySet:
    return Tutor.objects.annotate(
        global_id=F('person__global_id'),
        first_name=F('person__first_name'),
        last_name=F('person__last_name')
    ).values(
        'global_id',
        'first_name',
        'last_name'
    )

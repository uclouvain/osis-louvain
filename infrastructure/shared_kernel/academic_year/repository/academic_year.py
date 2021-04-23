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

from base.models.academic_year import AcademicYear as AcademicYearDatabase
from ddd.logic.shared_kernel.academic_year.builder.academic_year_builder import AcademicYearBuilder
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from ddd.logic.shared_kernel.academic_year.dtos import AcademicYearDataDTO
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from osis_common.ddd.interface import RootEntity, EntityIdentity, ApplicationService


class AcademicYearRepository(IAcademicYearRepository):
    @classmethod
    def get(cls, entity_id: AcademicYearIdentity) -> 'AcademicYear':
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List['AcademicYearIdentity']] = None, **kwargs) -> List['AcademicYear']:
        objects_as_dict = _get_common_queryset().values(
            'year',
            'start_date',
            'end_date',
        )
        return [
            AcademicYearBuilder.build_from_repository_dto(AcademicYearDataDTO(**obj_as_dict))
            for obj_as_dict in objects_as_dict
        ]

    @classmethod
    def delete(cls, entity_id: 'AcademicYearIdentity', **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def save(cls, entity: 'AcademicYear') -> None:
        raise NotImplementedError


def _get_common_queryset():
    return AcademicYearDatabase.objects.all()

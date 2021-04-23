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

from django.db.models import F

from ddd.logic.shared_kernel.language.builder.language_builder import LanguageBuilder
from ddd.logic.shared_kernel.language.domain.model.language import Language
from ddd.logic.shared_kernel.language.dtos import LanguageDataDTO
from ddd.logic.shared_kernel.language.repository.i_language import ILanguageRepository
from osis_common.ddd.interface import RootEntity, EntityIdentity, ApplicationService
from reference.models.language import Language as LanguageDatabase


class LanguageRepository(ILanguageRepository):
    @classmethod
    def get(cls, entity_id: EntityIdentity) -> RootEntity:
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[Language]:
        objects_as_dict = _get_common_queryset().annotate(
            code_iso=F('code'),
        ).values(
            'code_iso',
            'name',
        )
        return [
            LanguageBuilder.build_from_repository_dto(LanguageDataDTO(**obj_as_dict))
            for obj_as_dict in objects_as_dict
        ]

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def save(cls, entity: RootEntity) -> None:
        raise NotImplementedError


def _get_common_queryset():
    return LanguageDatabase.objects.all()

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

from base.models.entity_version import EntityVersion as EntityVersionDatabase
from base.models.enums import organization_type
from ddd.logic.learning_unit.builder.ucl_entity_builder import UclEntityBuilder
from ddd.logic.learning_unit.domain.model.responsible_entity import UCLEntityIdentity, UclEntity
from ddd.logic.learning_unit.dtos import UclEntityDataDTO
from ddd.logic.learning_unit.repository.i_ucl_entity import IUclEntityRepository
from osis_common.ddd.interface import EntityIdentity, ApplicationService, Entity, RootEntity


class UclEntityRepository(IUclEntityRepository):
    @classmethod
    def save(cls, entity: RootEntity) -> None:
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'UCLEntityIdentity') -> 'UclEntity':
        entity_version_as_dict = _get_common_queryset().filter(
            acronym=entity_id.code
        ).annotate(
            code=F('acronym'),
            type=F('entity_type'),
        ).values(
            'code',
            'type',
        ).get()
        dto = UclEntityDataDTO(**entity_version_as_dict)
        return UclEntityBuilder.build_from_repository_dto(dto)

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[Entity]:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError


def _get_common_queryset():
    return EntityVersionDatabase.objects.filter(
        entity__organization__type=organization_type.MAIN,
    )

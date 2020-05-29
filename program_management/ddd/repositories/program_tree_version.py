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

from django.db.models import F

from education_group.models.group_year import GroupYear
from osis_common.ddd import interface
from program_management.ddd.business_types import *
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.domain.program_tree_version import ProgramTreeVersion
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.models.education_group_version import EducationGroupVersion


class ProgramTreeVersionRepository(interface.AbstractRepository):

    @classmethod
    def create(cls, entity: 'ProgramTreeVersion') -> 'ProgramTreeVersionIdentity':
        raise NotImplementedError

    @classmethod
    def update(cls, entity: 'ProgramTreeVersion') -> 'ProgramTreeVersionIdentity':
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: ProgramTreeVersionIdentity) -> 'ProgramTreeVersion':
        qs = EducationGroupVersion.objects.filter(
            version_name=entity_id.version_name,
            offer__acronym=entity_id.offer_acronym,
            offer__academic_year__year=entity_id.year,
            is_transition=entity_id.is_transition,
        ).annotate(
            code=F('root_group__partial_acronym'),
            offer_acronym=F('offer__acronym'),
            offer_year=F('offer__academic_year__year'),
            version_title_fr=F('title_fr'),
            version_title_en=F('title_en'),
        ).values(
            'code',
            'offer_acronym',
            'offer_year',
            'version_name',
            'version_title_fr',
            'version_title_en',
            'is_transition',
        )
        if qs:
            return _instanciate_tree_version(qs[0])

    @classmethod
    def search(
            cls,
            entity_ids: Optional[List['ProgramTreeVersionIdentity']] = None,
            **kwargs
    ) -> List[ProgramTreeVersion]:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'ProgramTreeVersionIdentity') -> None:
        raise NotImplementedError

    @classmethod
    def search_all_versions_from_root_node(cls, root_node_identity: 'NodeIdentity') -> List['ProgramTreeVersion']:
        qs = GroupYear.objects.filter(
            partial_acronym=root_node_identity.code,
            academic_year__year=root_node_identity.year,
        ).order_by(
            'educationgroupversion__version_name'
        ).annotate(
            code=F('partial_acronym'),
            offer_acronym=F('educationgroupversion__offer__acronym'),
            offer_year=F('educationgroupversion__offer__academic_year__year'),
            version_name=F('educationgroupversion__version_name'),
            version_title_fr=F('educationgroupversion__title_fr'),
            version_title_en=F('educationgroupversion__title_en'),
            is_transition=F('educationgroupversion__is_transition'),
        ).values(
            'code',
            'offer_acronym',
            'offer_year',
            'version_name',
            'version_title_fr',
            'version_title_en',
            'is_transition',
        )
        results = []
        for record_dict in qs:
            results.append(_instanciate_tree_version(record_dict))
        return results


def _instanciate_tree_version(record_dict: dict) -> 'ProgramTreeVersion':

    return ProgramTreeVersion(
        entity_identity=ProgramTreeVersionIdentity(
            record_dict['offer_acronym'],
            record_dict['offer_year'],
            record_dict['version_name'],
            record_dict['is_transition'],
        ),
        program_tree_identity=ProgramTreeIdentity(record_dict['code'], record_dict['offer_year']),
        program_tree_repository=ProgramTreeRepository(),
        title_fr=record_dict['version_title_fr'],
        title_en=record_dict['version_title_en'],
    )

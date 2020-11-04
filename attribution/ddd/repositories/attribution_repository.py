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

from attribution.ddd.domain.attribution import AttributionIdentity, Attribution
from attribution.ddd.repositories.load_attribution import load_attributions
from osis_common.ddd import interface


class AttributionRepository(interface.AbstractRepository):

    @classmethod
    def search(cls, entity_ids: Optional[List['AttributionIdentity']] = None, **kwargs) -> List[Attribution]:
        return load_attributions(learning_unit_year_ids=kwargs.pop('learning_unit_year_ids'))

    @classmethod
    def delete(cls, entity_id: 'AttributionIdentity', **_) -> None:
        raise NotImplementedError

    @classmethod
    def create(cls, program_tree: 'AttributionIdentity', **_) -> 'AttributionIdentity':
        raise NotImplementedError

    @classmethod
    def update(cls, program_tree: 'AttributionIdentity', **_) -> 'AttributionIdentity':
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'AttributionIdentity') -> 'Attribution':
        raise NotImplementedError

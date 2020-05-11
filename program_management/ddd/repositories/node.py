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

from osis_common.ddd import interface
from osis_common.ddd.interface import EntityIdentity, Entity
from program_management.ddd.business_types import *
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.repositories import persist_tree, load_tree, load_node
from program_management.models.element import Element

from django.db.models import F, Value, Q, Case, When, IntegerField


class NodeRepository(interface.AbstractRepository):

    @classmethod
    def search_nodes_next_year(cls, node_pks: List[int], next_year: int) -> List['Node']:

        qs = Element.objects.filter(
            pk__in=node_pks
        ).filter(
            Q(group_year__group__groupyear__academic_year__year=next_year)
            | Q(learning_unit_year__learning_unit__learningunityear__academic_year__year=next_year)
        ).distinct().annotate(
            equivalent_element_id_from_year=Case(
                When(
                    group_year__group__groupyear__element__pk__isnull=False,
                    then=F('group_year__group__groupyear__element__pk')
                ),
                When(
                    learning_unit_year__learning_unit__learningunityear__element__pk__isnull=False,
                    then=F('learning_unit_year__learning_unit__learningunityear__element__pk')
                ),
                default=Value(-1),
                output_field=IntegerField(),
            )
        ).values_list(
            'equivalent_element_id_from_year',
            flat=True
        )
        if not qs:
            return []
        return load_node.load_multiple(qs)

    # @classmethod
    # def search(
    #         cls,
    #         entity_ids: Optional[List['NodeIdentity']] = None,
    #         year: int = None,
    #
    # ) -> List['Node']:
    #     pass


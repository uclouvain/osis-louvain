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
from typing import List, Dict

from django.db.models import F, Value, Q, Case, When, IntegerField

from program_management.ddd.business_types import *
from program_management.ddd.repositories import load_node
from program_management.models.element import Element

SearchFrom = Node
NodeIntoSearchedYear = Node


def search_nodes_next_year(
        search_from: List['NodeIdentity'],
        search_into_year: int
) -> Dict[SearchFrom, NodeIntoSearchedYear]:
    qs = Element.objects.all()

    filter_search_from = __build_where_clause(search_from[0])
    for identity in search_from[1:]:
        filter_search_from |= __build_where_clause(identity)

    qs = qs.filter(
        filter_search_from
    ).filter(
        Q(group_year__group__groupyear__academic_year__year=search_into_year)
        | Q(learning_unit_year__learning_unit__learningunityear__academic_year__year=search_into_year)
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
        ),
        search_from_code=Case(
            When(group_year_id__isnull=False, then=F('group_year__partial_acronym')),
            When(learning_unit_year_id__isnull=False, then=F('learning_unit_year__acronym')),
        ),
        search_from_year=Case(
            When(group_year_id__isnull=False, then=F('group_year__academic_year__year')),
            When(learning_unit_year_id__isnull=False, then=F('learning_unit_year__academic_year__year')),
        ),
        search_into_code=Case(
            When(group_year_id__isnull=False, then=F('group_year__partial_acronym')),
            When(learning_unit_year_id__isnull=False, then=F('learning_unit_year__acronym')),
        ),

    ).values_list(
        'code',
        'equivalent_element_id_from_year',
    )
    if not qs:
        return dict()
    return load_node.load_multiple(qs)


def test():
    from program_management.ddd.domain.node import NodeIdentity
    return search([NodeIdentity(code='LDROI1001', year=2019)])


def search(search_from: List['NodeIdentity']):
    qs = Element.objects.all()
    filter_search_from = __build_where_clause(search_from[0])
    for identity in search_from[1:]:
        filter_search_from |= __build_where_clause(identity)
    qs = qs.filter(filter_search_from)
    return qs


def __build_where_clause(node_identity: 'NodeIdentity') -> Q:
    return Q(
        Q(
            group_year__partial_acronym=node_identity.code,
            group_year__academic_year__year=node_identity.year
        ) & Q(
            learning_unit_year__acronym=node_identity.code,
            learning_unit_year__academic_year__year=node_identity.year
        )
    )

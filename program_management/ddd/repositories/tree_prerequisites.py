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
import itertools
from typing import List
from typing import Optional

from django.db.models import Subquery, OuterRef, F, Q

from base.models.enums import prerequisite_operator
from base.models.learning_unit_year import LearningUnitYear
from base.models.prerequisite_item import PrerequisiteItem as PrerequisiteItemModel
from osis_common.ddd import interface
from osis_common.ddd.interface import Entity, EntityIdentity, ApplicationService
from program_management.ddd.business_types import *
from program_management.ddd.domain import prerequisite as prerequisite_domain
from program_management.ddd.domain.prerequisite import Prerequisites
from program_management.models.element import Element

TreeRootId = int


class TreePrerequisitesRepository(interface.AbstractRepository):
    @classmethod
    def create(cls, entity: Entity, **kwargs: ApplicationService) -> EntityIdentity:
        raise NotImplementedError

    @classmethod
    def update(cls, entity: Entity, **kwargs: ApplicationService) -> EntityIdentity:
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'ProgramTreeIdentity') -> 'Prerequisites':
        tree_root_ids = Element.objects.filter(
            group_year__partial_acronym=entity_id.code,
            group_year__academic_year__year=entity_id.year,
        ).values_list('pk', flat=True)
        prerequisites_list = cls.search(tree_root_ids=tree_root_ids)
        if prerequisites_list:
            return prerequisites_list[0]

    @classmethod
    def search(
            cls,
            entity_ids: Optional[List['EntityIdentity']] = None,
            learning_unit_nodes: List['NodeLearningUnitYear'] = None,
            tree_root_ids: List['TreeRootId'] = None
    ) -> List['Prerequisites']:
        qs = PrerequisiteItemModel.objects
        if entity_ids:
            raise NotImplementedError
        if learning_unit_nodes:
            node_pks = set(n.pk for n in learning_unit_nodes)
            qs = qs.filter(
                Q(prerequisite__learning_unit_year_id__element__pk__in=node_pks)
                | Q(learning_unit__learningunityear__element__pk__in=node_pks)
            )
        if tree_root_ids:
            qs = qs.filter(prerequisite__education_group_version__root_group__element__id__in=tree_root_ids)

        return _transform_model_to_domain(qs.distinct())

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError


def _transform_model_to_domain(prerequisite_item_queryset) -> List['Prerequisites']:
    # FIXME :: cyclic import
    from program_management.ddd.domain.program_tree import ProgramTreeIdentity
    from program_management.ddd.domain.node import NodeIdentity
    prerequisite_item_queryset = prerequisite_item_queryset.annotate(
        code=Subquery(
            LearningUnitYear.objects.filter(
                learning_unit_id=OuterRef('learning_unit_id'),
                academic_year_id=OuterRef('prerequisite__learning_unit_year__academic_year_id'),
            ).values('acronym')[:1]
        ),
        year=F('prerequisite__learning_unit_year__academic_year__year'),
        main_operator=F('prerequisite__main_operator'),
        element_id=F('prerequisite__learning_unit_year__element__pk'),
        element_code=F('prerequisite__learning_unit_year__acronym'),
        root_element_id=F('prerequisite__education_group_version__root_group__element__pk'),
        root_code=F('prerequisite__education_group_version__root_group__partial_acronym'),
        root_year=F('prerequisite__education_group_version__root_group__academic_year__year'),
    ).order_by(
        'root_element_id',
        'element_id',
        'group_number',
        'position'
    ).values(
        'root_element_id',
        'root_code',
        'root_year',
        'element_id',
        'element_code',
        'main_operator',
        'group_number',
        'position',
        'code',
        'year'
    )

    result = []

    result_grouped_by_ed_group_id = itertools.groupby(prerequisite_item_queryset, key=lambda p: p['root_element_id'])
    for program_id, prerequisite_item_list in result_grouped_by_ed_group_id:
        prerequisites_dict = {}
        result_grouped_by_learn_unit_id = itertools.groupby(
            prerequisite_item_list,
            key=lambda p: p['element_id']
        )
        for node_id, prequisite_items in result_grouped_by_learn_unit_id:
            prequisite_items = list(prequisite_items)

            first_item = prequisite_items[0]
            node_identity = NodeIdentity(code=first_item['element_code'], year=first_item['year'])
            preq = prerequisite_domain.Prerequisite(
                main_operator=first_item['main_operator'],
                node_having_prerequisites=node_identity,
                context_tree=ProgramTreeIdentity(code=first_item['root_code'], year=first_item['root_year'])
            )
            prerequisites_dict.setdefault(node_identity, preq)
            for _, p_items in itertools.groupby(prequisite_items, key=lambda p: p['group_number']):
                operator_item = prerequisite_operator.OR if preq.main_operator == prerequisite_operator.AND else \
                    prerequisite_operator.AND
                p_group_items = prerequisite_domain.PrerequisiteItemGroup(
                    operator=operator_item,
                    prerequisite_items=[
                        prerequisite_domain.PrerequisiteItem(p_item['code'], p_item['year']) for p_item in p_items
                    ]
                )
                prerequisites_dict[node_identity].add_prerequisite_item_group(p_group_items)

        prerequisite_list = list(prerequisites_dict.values())
        result.append(
            Prerequisites(
                context_tree=prerequisite_list[0].context_tree,
                prerequisites=prerequisite_list,
            )
        )
    return result

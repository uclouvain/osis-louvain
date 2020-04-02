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

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Subquery, OuterRef, F

from base.models.enums import prerequisite_operator
from base.models.learning_unit_year import LearningUnitYear
from base.models.prerequisite_item import PrerequisiteItem
from program_management.ddd.domain import prerequisite


def load_has_prerequisite(tree_root_id: int, node_ids: List[int]) -> dict:
    """
    This function return a dict of prerequisite grouped by node_id
    Ex: {
       node_id:  Prerequisite,
       ... : Prerequisite,
    }
    :param tree_root_id: Root node of the tree
    :param node_ids: List of id node which we want to check data
    :return:
    """
    prerequisite_item_qs = PrerequisiteItem.objects.filter(
        prerequisite__education_group_year_id=tree_root_id,
        prerequisite__learning_unit_year_id__in=node_ids
    ).annotate(
        acronym=Subquery(
            LearningUnitYear.objects.filter(
                learning_unit_id=OuterRef('learning_unit_id'),
                academic_year_id=OuterRef('prerequisite__learning_unit_year__academic_year_id'),
            ).values('acronym')[:1]
        ),
        year=F('prerequisite__learning_unit_year__academic_year__year'),
        main_operator=F('prerequisite__main_operator'),
        learning_unit_year_id=F('prerequisite__learning_unit_year_id')
    ).order_by('learning_unit_year_id', 'group_number', 'position')\
     .values('learning_unit_year_id', 'main_operator', 'group_number', 'position', 'acronym', 'year')

    prerequisites_dict = {}
    for node_id, prequisite_items in itertools.groupby(prerequisite_item_qs, key=lambda p: p['learning_unit_year_id']):
        prequisite_items = list(prequisite_items)

        preq = prerequisite.Prerequisite(main_operator=prequisite_items[0]['main_operator'])
        prerequisites_dict.setdefault(node_id, preq)
        for _, p_items in itertools.groupby(prequisite_items, key=lambda p: p['group_number']):
            operator_item = prerequisite_operator.OR if preq.main_operator == prerequisite_operator.AND else \
                prerequisite_operator.AND
            p_group_items = prerequisite.PrerequisiteItemGroup(
                operator=operator_item,
                prerequisite_items=[
                    prerequisite.PrerequisiteItem(p_item['acronym'], p_item['year']) for p_item in p_items
                ]
            )
            prerequisites_dict[node_id].add_prerequisite_item_group(p_group_items)
    return prerequisites_dict


def load_is_prerequisite(tree_root_id: int, node_ids: List[int]) -> dict:
    """
    By node_id, compute the fact that this node is prerequisite of another node
        Ex: {
           node_id:  [node_id, node_id, ...],
           node_id:  [node_id],
        }
    :param tree_root_id: Root node of the tree
    :param node_ids: List of id node
    :return:
    """
    qs = PrerequisiteItem.objects.filter(
        prerequisite__education_group_year_id=tree_root_id,
        learning_unit__learningunityear__pk__in=node_ids
    ).values('learning_unit__learningunityear__pk')\
     .annotate(
        node_id=F('learning_unit__learningunityear__pk'),
        is_a_prerequisite_of=ArrayAgg('prerequisite__learning_unit_year_id'),
     )

    return {result['node_id']: result['is_a_prerequisite_of'] for result in qs}

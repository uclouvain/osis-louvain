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
from typing import List, Dict

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Subquery, OuterRef, F

from base.models.enums import prerequisite_operator
from base.models.learning_unit_year import LearningUnitYear
from base.models.prerequisite_item import PrerequisiteItem as PrerequisiteItemModel
from program_management.ddd.domain import prerequisite as prerequisite_domain
from program_management.models.enums.node_type import NodeType

from program_management.ddd.business_types import *

TreeRootId = int
NodeId = int
LearningUnitYearId = int
IsPrerequisiteOfNodeId = int


def load_has_prerequisite_multiple(
        tree_root_ids: List[int],
        nodes: Dict[str, 'Node']
) -> Dict[TreeRootId, Dict[NodeId, prerequisite_domain.Prerequisite]]:
    """
    This function return a dict of prerequisite grouped by node_id
    Ex: {
       node_id:  Prerequisite,
       ... : Prerequisite,
    }
    :param tree_root_ids: List of root nodes of the trees
    :param nodes: Dict where keys = '<node_id>_<TYPE>' and values = Node
    :return:
    """
    prerequisite_item_qs = PrerequisiteItemModel.objects.filter(
        prerequisite__education_group_year_id__in=tree_root_ids,
        prerequisite__learning_unit_year_id__in=set(n.pk for n in nodes.values() if n.is_learning_unit())
    ).annotate(
        code=Subquery(
            LearningUnitYear.objects.filter(
                learning_unit_id=OuterRef('learning_unit_id'),
                academic_year_id=OuterRef('prerequisite__learning_unit_year__academic_year_id'),
            ).values('acronym')[:1]
        ),
        year=F('prerequisite__learning_unit_year__academic_year__year'),
        main_operator=F('prerequisite__main_operator'),
        learning_unit_year_id=F('prerequisite__learning_unit_year_id'),
        education_group_year_id=F('prerequisite__education_group_year_id'),
    ).order_by(
        'learning_unit_year_id',
        'group_number',
        'position'
    ).values(
        'education_group_year_id',
        'learning_unit_year_id',
        'main_operator',
        'group_number',
        'position',
        'code',
        'year'
    )

    prerequisites_dict_by_program_root_id = {}
    result_grouped_by_ed_group_id = itertools.groupby(prerequisite_item_qs, key=lambda p: p['education_group_year_id'])
    for program_id, prerequisite_item_list in result_grouped_by_ed_group_id:
        prerequisites_dict = {}
        result_grouped_by_learn_unit_id = itertools.groupby(
            prerequisite_item_list,
            key=lambda p: p['learning_unit_year_id']
        )
        for node_id, prequisite_items in result_grouped_by_learn_unit_id:
            prequisite_items = list(prequisite_items)

            preq = prerequisite_domain.Prerequisite(main_operator=prequisite_items[0]['main_operator'])
            prerequisites_dict.setdefault(node_id, preq)
            for _, p_items in itertools.groupby(prequisite_items, key=lambda p: p['group_number']):
                operator_item = prerequisite_operator.OR if preq.main_operator == prerequisite_operator.AND else \
                    prerequisite_operator.AND
                p_group_items = prerequisite_domain.PrerequisiteItemGroup(
                    operator=operator_item,
                    prerequisite_items=[
                        prerequisite_domain.PrerequisiteItem(p_item['code'], p_item['year']) for p_item in p_items
                    ]
                )
                prerequisites_dict[node_id].add_prerequisite_item_group(p_group_items)
        prerequisites_dict_by_program_root_id[program_id] = prerequisites_dict
    return prerequisites_dict_by_program_root_id


def load_is_prerequisite_multiple(
        tree_root_ids: List[int],
        nodes: Dict['NodeKey', 'Node']
) -> Dict[TreeRootId, Dict[NodeId, List['NodeLearningUnitYear']]]:
    """
    By node_id, compute the fact that this node is prerequisite of another node
        Ex: {
           node_id:  [node_id, node_id, ...],
           node_id:  [node_id],
        }
    :param tree_root_ids: List of root nodes of the trees
    :param nodes: Dict where keys = '<node_id>_<TYPE>' and values = Node
    :return:
    """
    qs = PrerequisiteItemModel.objects.filter(
        prerequisite__education_group_year_id__in=tree_root_ids,
        learning_unit__learningunityear__pk__in=set(n.pk for n in nodes.values() if n.is_learning_unit())
    ).values(
        'learning_unit__learningunityear__pk'
    ).annotate(
        node_id=F('learning_unit__learningunityear__pk'),
        is_a_prerequisite_of=ArrayAgg('prerequisite__learning_unit_year_id'),
        education_group_year_id=F('prerequisite__education_group_year_id'),
    ).values(
        'node_id',
        'is_a_prerequisite_of',
        'education_group_year_id',
    )

    result = {}
    for tree_root_id, prerequisite_query_result in itertools.groupby(qs, key=lambda p: p['education_group_year_id']):
        map_node_id_with_ids_prerequisite_of = __get_is_prerequisite_of_by_node_id(prerequisite_query_result)
        result[tree_root_id] = __convert_ids_to_nodes(map_node_id_with_ids_prerequisite_of, nodes)
    return result


def __get_is_prerequisite_of_by_node_id(prerequisite_query_result) -> Dict[NodeId, List[IsPrerequisiteOfNodeId]]:
    return {
        prerequisite_result['node_id']: prerequisite_result['is_a_prerequisite_of']
        for prerequisite_result in prerequisite_query_result
    }


def __convert_ids_to_nodes(
        map_node_id_with_is_prerequisite: Dict[NodeId, List[IsPrerequisiteOfNodeId]],
        nodes: Dict['NodeKey', 'Node']
) -> Dict[NodeId, List['NodeLearningUnitYear']]:
    return {
        main_node_id: [nodes['{}_{}'.format(id, NodeType.LEARNING_UNIT)] for id in node_ids]
        for main_node_id, node_ids in map_node_id_with_is_prerequisite.items()
    }

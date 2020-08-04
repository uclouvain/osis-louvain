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
import time
from typing import List, Set, Dict

from django.db import transaction
from django.db.models import Q, F

from base.models.enums.link_type import LinkTypes
from base.models.group_element_year import GroupElementYear
from osis_common.decorators.deprecated import deprecated
from program_management.ddd.business_types import *
from program_management.ddd.repositories import _persist_prerequisite
from program_management.models.element import Element


ElementId = int


@deprecated  # use ProgramTreeRepository.create() or .update() instead
@transaction.atomic
def persist(tree: 'ProgramTree') -> None:
    __update_or_create_links(tree)
    __delete_links(tree, tree.root_node)
    _persist_prerequisite.persist(tree)


def __update_or_create_links(tree: 'ProgramTree'):
    links_has_changed = [
        link for link in tree.get_all_links() if link.has_changed
    ]
    elements_by_identity = __get_elements_by_node_identity(links_has_changed)
    for link in links_has_changed:
        __persist_group_element_year(link, elements_by_identity)


def __get_elements_by_node_identity(links_has_changed: List['Link']) -> Dict['NodeIdentity', ElementId]:
    nodes = {link.parent for link in links_has_changed} | {link.child for link in links_has_changed}

    group_elements = __get_elements_as_group(nodes)
    learning_unit_elements = __get_elements_as_learning_unit(nodes)

    result = {}
    for node in nodes:
        elements = group_elements
        if node.is_learning_unit():
            elements = learning_unit_elements

        element = next(elem for elem in elements if elem['code'] == node.code and elem['year'] == node.year)
        result[node.entity_id] = element['pk']

    return result


def __get_elements_as_group(nodes: Set['Node']):
    group_nodes = {node for node in nodes if node.is_group_or_mini_or_training()}
    return Element.objects.filter(
        group_year__partial_acronym__in={node.entity_id.code for node in group_nodes},
        group_year__academic_year__year__in={node.entity_id.year for node in group_nodes},
    ).annotate(
        code=F('group_year__partial_acronym'),
        year=F('group_year__academic_year__year'),
    ).values('pk', 'code', 'year')


def __get_elements_as_learning_unit(nodes: Set['Node']):
    learning_unit_nodes = {node for node in nodes if node.is_learning_unit()}
    return Element.objects.filter(
        learning_unit_year__acronym__in={node.entity_id.code for node in learning_unit_nodes},
        learning_unit_year__academic_year__year__in={node.entity_id.year for node in learning_unit_nodes},
    ).annotate(
        code=F('learning_unit_year__acronym'),
        year=F('learning_unit_year__academic_year__year'),
    ).values('pk', 'code', 'year')


def __persist_group_element_year(link: 'Link', elements_by_identity: Dict['NodeIdentity', ElementId]):
    group_element_year, _ = GroupElementYear.objects.update_or_create(
        parent_element_id=elements_by_identity[link.parent.entity_id],
        child_element_id=elements_by_identity[link.child.entity_id],
        defaults={
            'relative_credits': link.relative_credits,
            'min_credits': link.min_credits,
            'max_credits': link.max_credits,
            'is_mandatory': link.is_mandatory,
            'block': link.block,
            'access_condition': link.access_condition,
            'comment': link.comment,
            'comment_english': link.comment_english,
            'own_comment': link.own_comment,
            'quadrimester_derogation': link.quadrimester_derogation,
            # FIXME : Find a rules for enum in order to be consistant
            'link_type': link.link_type.name if isinstance(link.link_type, LinkTypes) else link.link_type,
            'order': link.order,

        }
    )


def __delete_links(tree: 'ProgramTree', node: 'Node'):
    for link in node._deleted_children:
        __persist_deleted_prerequisites(tree, link.child)
        __delete_group_element_year(link)
    for link in node.children:
        __delete_links(tree, link.child)


def __persist_deleted_prerequisites(tree: 'ProgramTree', node: 'Node'):
    if node.is_learning_unit():
        _persist_prerequisite._persist(tree.root_node, node)
    else:
        for child_node in node.get_all_children_as_learning_unit_nodes():
            _persist_prerequisite._persist(tree.root_node, child_node)


def __delete_group_element_year(link):
    GroupElementYear.objects.filter(pk=link.pk).delete()

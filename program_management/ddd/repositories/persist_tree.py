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
from django.db import transaction
from django.db.models import Q

from base.models.group_element_year import GroupElementYear
from program_management.ddd.domain import program_tree
from program_management.ddd.domain.node import Node, NodeEducationGroupYear, NodeLearningUnitYear


@transaction.atomic
def persist(tree: program_tree.ProgramTree) -> None:
    __update_or_create_links(tree.root_node)
    __delete_links(tree.root_node)


def __update_or_create_links(node: Node):
    for link in node.children:
        # methode update_or_create doesn't work with outer-join on PostgreSQL
        group_element_year, _ = GroupElementYear.objects.get_or_create(
            parent_id=link.parent.pk,
            child_branch_id=link.child.pk if isinstance(link.child, NodeEducationGroupYear) else None,
            child_leaf_id=link.child.pk if isinstance(link.child, NodeLearningUnitYear) else None,
        )
        group_element_year.relative_credits = link.relative_credits
        group_element_year.min_credits = link.min_credits
        group_element_year.max_credits = link.max_credits
        group_element_year.is_mandatory = link.is_mandatory
        group_element_year.block = link.block
        group_element_year.access_condition = link.access_condition
        group_element_year.comment = link.comment
        group_element_year.comment_english = link.comment_english
        group_element_year.own_comment = link.own_comment
        group_element_year.quadrimester_derogation = link.quadrimester_derogation
        group_element_year.link_type = link.link_type
        group_element_year.save()

        __update_or_create_links(link.child)


def __delete_links(node: Node):
    child_ids = [link.child.pk for link in node.children]

    GroupElementYear.objects.filter(parent_id=node.pk).exclude(
        Q(child_branch_id__in=child_ids) | Q(child_leaf_id__in=child_ids)   # TODO: Quick fix before migration
    ).delete()

    for link in node.children:
        __delete_links(link.child)

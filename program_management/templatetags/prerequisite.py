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
import collections
from typing import List

from django import template, urls
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from program_management.ddd.domain import link
from program_management.ddd.domain import node
from program_management.ddd.domain.prerequisite import Prerequisite, PrerequisiteItem, PrerequisiteItemGroup

register = template.Library()


@register.simple_tag
def prerequisite_as_html(prerequisite: Prerequisite, links: List[link.Link]):
    if not prerequisite:
        return "-"

    def _format_group(group: PrerequisiteItemGroup):
        return "({})" if len(group.prerequisite_items) > 1 and len(prerequisite.prerequisite_item_groups) > 1 else "{}"

    result = str(" " + _(prerequisite.main_operator) + " ").join(
        _format_group(group).format(_prerequisite_group_as_html(group, links))
        for group in prerequisite.prerequisite_item_groups
    )
    return mark_safe(result) or "-"


def _prerequisite_group_as_html(prerequisite_group: PrerequisiteItemGroup, links: List[link.Link]):
    return str(" " + _(prerequisite_group.operator) + " ").join(_prerequisite_item_as_html(p_item, links)
                                                                for p_item in prerequisite_group.prerequisite_items)


def _prerequisite_item_as_html(prerequisite_item: PrerequisiteItem, links: List[link.Link]):
    item_link = next(
        (link_obj for link_obj in links
         if link_obj.child.code == prerequisite_item.code and link_obj.child.year == prerequisite_item.year
         ),
        None
    )

    title = "{}\n{} : {} / {}".format(
        item_link.child.title,
        _('Cred. rel./abs.'),
        item_link.relative_credits or '-',
        item_link.child.credits.normalize()
    ) if item_link else ""
    return "<a href='{url}' title='{title}'>{code}</a>".format(
        url=urls.reverse("learning_unit", kwargs={"acronym": prerequisite_item.code, "year": prerequisite_item.year}),
        title=title,
        code=prerequisite_item.code
    )


IsPrerequisiteRow = collections.namedtuple('IsPrerequisiteRow', 'code year title relative_credits credits')


@register.inclusion_tag("program_management/templatetags/prerequisite/is_prerequisite.html", takes_context=False)
def is_prerequisite_as_html(is_prerequisite_list: List[node.NodeLearningUnitYear], links: List[link.Link]):
    rows = []
    for node_obj in is_prerequisite_list:
        first_link_occurence = next(
            (link_obj for link_obj in links if link_obj.child.node_id == node_obj.node_id),
            None
        )
        relative_credits = (first_link_occurence and first_link_occurence.relative_credits) or "-"
        row = IsPrerequisiteRow(
            node_obj.code, str(node_obj.year), node_obj.title, str(relative_credits), str(node_obj.credits.normalize())
        )
        rows.append(row)
    return {"is_prerequisite_rows": rows}

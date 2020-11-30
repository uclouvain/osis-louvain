# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django.db.models import Count

from base.models.group_element_year import GroupElementYear

YEAR_FROM = 2019


def fix_order(*args, **kwargs):
    problematic_element_parents = find_problematic_parents()

    print("Problematic parents: {}".format(len(problematic_element_parents)))

    for parent_element_id in problematic_element_parents:
        reorder_children(parent_element_id)
        print(str(parent_element_id))


def find_problematic_parents():
    return GroupElementYear.objects.filter(
        parent_element__group_year__academic_year__year__gte=YEAR_FROM
    ).values(
        "parent_element",
        "order",
    ).annotate(
        num_children_order=Count("order")
    ).filter(
        num_children_order__gt=1
    ).values_list("parent_element", flat=True)


def reorder_children(parent_element_id: int):
    links = GroupElementYear.objects.filter(parent_element__id=parent_element_id).order_by("order")
    for order, link in enumerate(links, start=1):
        link.order = order
        link.save()

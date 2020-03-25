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
from typing import List

from base.models.enums import prerequisite_operator

PrerequisiteExpression = str  # Example : "(Prerequisite1 OR Prerequisite2) AND (prerequisite3)"


class PrerequisiteItem:
    def __init__(self, acronym: str, year: int):
        self.acronym = acronym
        self.year = year

    def __str__(self):
        return self.acronym


class PrerequisiteItemGroup:
    def __init__(self, operator: str, prerequisite_items: List[PrerequisiteItem] = None):
        assert operator in [prerequisite_operator.OR, prerequisite_operator.AND]
        self.operator = operator
        self.prerequisite_items = prerequisite_items or []

    def add_prerequisite_item(self, acronym: str, year: int):
        self.prerequisite_items.append(PrerequisiteItem(acronym, year))

    def __str__(self):
        return str(" " + self.operator + " ").join(str(p_item) for p_item in self.prerequisite_items)


class Prerequisite:
    def __init__(self, main_operator: str, prerequisite_item_groups: List[PrerequisiteItemGroup] = None):
        assert main_operator in [prerequisite_operator.OR, prerequisite_operator.AND]
        self.main_operator = main_operator

        self.prerequisite_item_groups = prerequisite_item_groups or []

    def add_prerequisite_item_group(self, group: PrerequisiteItemGroup):
        self.prerequisite_item_groups.append(group)

    def __str__(self) -> PrerequisiteExpression:
        str_format = "({})" if len(self.prerequisite_item_groups) > 1 else "{}"
        return str(" " + self.main_operator + " ").join(
            str_format.format(group) for group in self.prerequisite_item_groups
        )

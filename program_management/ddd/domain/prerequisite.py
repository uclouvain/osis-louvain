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
from typing import List, Set
import re
from typing import List

from base.models import learning_unit
from base.models.enums import prerequisite_operator
from base.models.enums.prerequisite_operator import OR, AND
from django.utils.translation import gettext as _


AND_OPERATOR = "ET"
OR_OPERATOR = 'OU'
ACRONYM_REGEX = learning_unit.LEARNING_UNIT_ACRONYM_REGEX_ALL.lstrip('^').rstrip('$')
NO_PREREQUISITE_REGEX = r''
UNIQUE_PREREQUISITE_REGEX = r'{acronym_regex}'.format(acronym_regex=ACRONYM_REGEX)
ELEMENT_REGEX = r'({acronym_regex}|\({acronym_regex}( {secondary_operator} {acronym_regex})+\))'
MULTIPLE_PREREQUISITES_REGEX = '{element_regex}( {main_operator} {element_regex})+'
MULTIPLE_PREREQUISITES_REGEX_OR = MULTIPLE_PREREQUISITES_REGEX.format(
    main_operator=OR_OPERATOR,
    element_regex=ELEMENT_REGEX.format(acronym_regex=ACRONYM_REGEX, secondary_operator=AND_OPERATOR)
)
MULTIPLE_PREREQUISITES_REGEX_AND = MULTIPLE_PREREQUISITES_REGEX.format(
    main_operator=AND_OPERATOR,
    element_regex=ELEMENT_REGEX.format(acronym_regex=ACRONYM_REGEX, secondary_operator=OR_OPERATOR)
)
PREREQUISITE_SYNTAX_REGEX = r'^(?i)({no_element_regex}|' \
                            r'{unique_element_regex}|' \
                            r'{multiple_elements_regex_and}|' \
                            r'{multiple_elements_regex_or})$'.format(
                                no_element_regex=NO_PREREQUISITE_REGEX,
                                unique_element_regex=UNIQUE_PREREQUISITE_REGEX,
                                multiple_elements_regex_and=MULTIPLE_PREREQUISITES_REGEX_AND,
                                multiple_elements_regex_or=MULTIPLE_PREREQUISITES_REGEX_OR
                            )

PrerequisiteExpression = str  # Example : "(Prerequisite1 OR Prerequisite2) AND (prerequisite3)"


class PrerequisiteItem:
    def __init__(self, code: str, year: int):
        self.code = code
        self.year = year

    def __str__(self):
        return self.code

    def __eq__(self, other):
        return self.code == other.code and self.year == other.year

    def __hash__(self):
        return hash(self.code + str(self.year))


class PrerequisiteItemGroup:
    def __init__(self, operator: str, prerequisite_items: List[PrerequisiteItem] = None):
        assert operator in [prerequisite_operator.OR, prerequisite_operator.AND]
        self.operator = operator
        self.prerequisite_items = prerequisite_items or []

    def add_prerequisite_item(self, code: str, year: int):
        self.prerequisite_items.append(PrerequisiteItem(code, year))

    def remove_prerequisite_item(self, prerequisite_item: 'PrerequisiteItem') -> bool:
        if prerequisite_item in self.prerequisite_items:
            self.prerequisite_items.remove(prerequisite_item)
            return True
        return False

    def __str__(self):
        return str(" " + _(self.operator) + " ").join(str(p_item) for p_item in self.prerequisite_items)


class Prerequisite:
    def __init__(self, main_operator: str, prerequisite_item_groups: List[PrerequisiteItemGroup] = None):
        assert main_operator in [prerequisite_operator.OR, prerequisite_operator.AND]
        self.main_operator = main_operator

        self.prerequisite_item_groups = prerequisite_item_groups or []
        self.has_changed = False

    def add_prerequisite_item_group(self, group: PrerequisiteItemGroup):
        self.prerequisite_item_groups.append(group)

    def get_all_prerequisite_items(self) -> List['PrerequisiteItem']:
        all_prerequisites = list()
        for prereq_item_group in self.prerequisite_item_groups:
            for item in prereq_item_group.prerequisite_items:
                all_prerequisites.append(item)
        return all_prerequisites

    def remove_all_prerequisite_items(self):
        for prerequisite_item in set(self.get_all_prerequisite_items()):
            self.remove_prerequisite_item(prerequisite_item.code, prerequisite_item.year)

    def remove_prerequisite_item(self, code: str, year: int) -> None:
        self.has_changed = any(
            prereq_item_group.remove_prerequisite_item(PrerequisiteItem(code=code, year=year))
            for prereq_item_group in self.prerequisite_item_groups
        )

    def __str__(self) -> PrerequisiteExpression:
        def _format_group(group: PrerequisiteItemGroup):
            return "({})" if len(group.prerequisite_items) > 1 and len(self.prerequisite_item_groups) > 1 else "{}"
        return str(" " + _(self.main_operator) + " ").join(
            _format_group(group).format(group) for group in self.prerequisite_item_groups
        )


class NullPrerequisite(Prerequisite):
    def __init__(self):
        super().__init__(prerequisite_operator.AND, None)

    def __bool__(self):
        return False

    def __str__(self):
        return ""


class PrerequisiteFactory:
    def from_expression(self, prerequisite_expression: PrerequisiteExpression, year: int) -> Prerequisite:
        if not prerequisite_expression:
            return NullPrerequisite()

        main_operator = self._detect_main_operator_in_string(prerequisite_expression)
        secondary_operator = AND if main_operator == OR else OR
        prerequisite_item_groups = self._get_grouped_items_from_string(
            prerequisite_expression,
            main_operator,
            secondary_operator,
            year
        )

        return Prerequisite(main_operator, prerequisite_item_groups)

    @classmethod
    def _get_grouped_items_from_string(
            cls,
            prerequisite_string: PrerequisiteExpression,
            main_operator: str,
            secondary_operator: str,
            year: int
    ) -> List[PrerequisiteItemGroup]:
        main_operator_splitter = ' ET ' if main_operator == AND else ' OU '
        secondary_operator_splitter = ' OU ' if main_operator == AND else ' ET '

        groups = prerequisite_string.split(main_operator_splitter)

        return [
            PrerequisiteItemGroup(
                secondary_operator,
                cls._split_group_into_items(group, secondary_operator_splitter, year)
            ) for group in groups
        ]

    @classmethod
    def _split_group_into_items(cls, group: str, operator: str, year: int) -> List[PrerequisiteItem]:
        group = cls._remove_parenthesis(group)
        group = group.split(operator)
        group_of_learning_units = [PrerequisiteItem(item, year) for item in group]
        return group_of_learning_units

    @classmethod
    def _remove_parenthesis(cls, string: str):
        return re.sub('[()]', "", string)

    @classmethod
    def _detect_main_operator_in_string(cls, prerequisite_string: PrerequisiteExpression) -> str:
        if re.match(MULTIPLE_PREREQUISITES_REGEX_OR, prerequisite_string):
            return OR
        return AND


factory = PrerequisiteFactory()

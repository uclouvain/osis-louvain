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
import contextlib
import re
from typing import List, Dict

import attr
from django.utils.translation import gettext as _

from base.models import learning_unit
from base.models.enums import prerequisite_operator
from base.models.enums.prerequisite_operator import OR, AND
from base.utils.cache import cached_result
from osis_common.ddd import interface
from program_management.ddd.business_types import *
from program_management.ddd.domain.exception import CannotCopyPrerequisiteException
from program_management.ddd.validators import validators_by_business_action

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

    def get_prerequisite_item_expression(self, translate: bool = True) -> PrerequisiteExpression:
        operator = _(self.operator) if translate else self.operator
        return str(" " + operator + " ").join(str(p_item) for p_item in self.prerequisite_items)

    def __str__(self) -> PrerequisiteExpression:
        return self.get_prerequisite_item_expression()


@attr.s(slots=True)
class Prerequisite(interface.Entity):

    main_operator = attr.ib(type=str)
    context_tree = attr.ib(type='ProgramTreeIdentity')
    node_having_prerequisites = attr.ib(type='NodeIdentity')
    prerequisite_item_groups = attr.ib(type=List[PrerequisiteItemGroup], factory=list)

    has_changed = attr.ib(type=bool, default=False)

    @main_operator.validator
    def _main_operator_validator(self, attribute, value):
        assert value in [prerequisite_operator.OR, prerequisite_operator.AND]

    def add_prerequisite_item_group(self, group: PrerequisiteItemGroup):
        self.prerequisite_item_groups.append(group)

    def get_all_prerequisite_items(self) -> List['PrerequisiteItem']:
        all_prerequisites = list()
        for prereq_item_group in self.prerequisite_item_groups:
            for item in prereq_item_group.prerequisite_items:
                all_prerequisites.append(item)
        return all_prerequisites

    def remove_all_prerequisite_items(self):
        self.prerequisite_item_groups = []
        self.has_changed = True

    def remove_prerequisite_item(self, code: str, year: int) -> None:
        self.has_changed = any(
            prereq_item_group.remove_prerequisite_item(PrerequisiteItem(code=code, year=year))
            for prereq_item_group in self.prerequisite_item_groups
        )

    def get_prerequisite_expression(self, translate: bool = True) -> PrerequisiteExpression:
        def _format_group(group: PrerequisiteItemGroup):
            return "({})" if len(group.prerequisite_items) > 1 and len(self.prerequisite_item_groups) > 1 else "{}"

        main_operator = _(self.main_operator) if translate else self.main_operator
        return str(" " + main_operator + " ").join(
            _format_group(group).format(group.get_prerequisite_item_expression(translate=translate))
            for group in self.prerequisite_item_groups
        )

    def __str__(self) -> PrerequisiteExpression:
        return self.get_prerequisite_expression()

    def secondary_operator(self):
        return OR if self.main_operator == AND else AND


class NullPrerequisite(Prerequisite):
    def __init__(self, context_tree: 'ProgramTreeIdentity', node_having_prerequisites: 'NodeIdentity'):
        super().__init__(
            main_operator=prerequisite_operator.AND,
            context_tree=context_tree,
            node_having_prerequisites=node_having_prerequisites,
            prerequisite_item_groups=None,
        )

    def __bool__(self):
        return False

    def __str__(self):
        return ""


class PrerequisiteFactory:
    def from_expression(
            self,
            prerequisite_expression: 'PrerequisiteExpression',
            node_having_prerequisites: 'NodeIdentity',
            context_tree: 'ProgramTreeIdentity'
    ) -> Prerequisite:
        if not prerequisite_expression:
            return NullPrerequisite(context_tree, node_having_prerequisites)

        main_operator = self._detect_main_operator_in_string(prerequisite_expression)
        secondary_operator = AND if main_operator == OR else OR
        prerequisite_item_groups = self._get_grouped_items_from_string(
            prerequisite_expression,
            main_operator,
            secondary_operator,
            node_having_prerequisites.year
        )

        result = Prerequisite(main_operator, context_tree, node_having_prerequisites, prerequisite_item_groups)
        result.has_changed = True
        return result

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

    @classmethod
    def copy_to_next_year(cls, to_copy: 'Prerequisite', next_year_tree: 'ProgramTree') -> 'Prerequisite':
        next_year_identity = attr.evolve(
            to_copy.node_having_prerequisites,
            year=to_copy.node_having_prerequisites.year+1
        )

        code_presents = {node.code for node in next_year_tree.get_all_nodes()}
        if next_year_identity.code not in code_presents:
            raise CannotCopyPrerequisiteException()

        items_code = {item.code for item in to_copy.get_all_prerequisite_items()}
        if items_code.difference(code_presents):
            raise CannotCopyPrerequisiteException()

        return cls().from_expression(
            cls._normalize_expression(to_copy.get_prerequisite_expression(translate=False)),
            next_year_identity,
            next_year_tree.entity_id
        )

    # FIX: Because the expression varies with translation
    @classmethod
    def _normalize_expression(cls, prerequisite_expression: str) -> str:
        return prerequisite_expression.replace(' AND ', ' ET ').replace(' OR ', ' OU ')


factory = PrerequisiteFactory()


class PrerequisitesBuilder:
    def copy_to_next_year(self, from_prerequisites: 'Prerequisites', to_tree: 'ProgramTree') -> 'Prerequisites':
        next_year_prerequisites = list()
        for prerequisite in from_prerequisites.prerequisites:
            with contextlib.suppress(CannotCopyPrerequisiteException):
                next_year_prerequisites.append(
                    factory.copy_to_next_year(prerequisite, to_tree)
                )
        return Prerequisites(to_tree.entity_id, next_year_prerequisites)


@attr.s(slots=True)
class Prerequisites(interface.RootEntity):
    context_tree = attr.ib(type='ProgramTreeIdentity')
    prerequisites = attr.ib(type=List[Prerequisite], factory=list)

    def has_prerequisites(self, node: 'NodeLearningUnitYear') -> bool:
        return bool(self.get_prerequisite(node))

    def is_prerequisite(self, node: 'NodeLearningUnitYear') -> bool:
        return bool(self.search_is_prerequisite_of(node))

    def search_is_prerequisite_of(self, search_from_node: 'NodeLearningUnitYear') -> List['NodeIdentity']:
        return self.__map_is_prerequisite_of().get(search_from_node.entity_id) or []

    def get_prerequisite(self, node: 'NodeLearningUnitYear') -> 'Prerequisite':
        return self._map_node_identity_prerequisite().get(node.entity_id)

    def set_prerequisite(
            self,
            node_having_prerequisites: 'NodeLearningUnitYear',
            prerequisite_expression: 'PrerequisiteExpression',
            context_tree: 'ProgramTree'
    ):
        is_valid, messages = self.__clean_set_prerequisite(
            prerequisite_expression,
            node_having_prerequisites,
            context_tree
        )
        if is_valid:
            new_prerequisite = factory.from_expression(
                prerequisite_expression=prerequisite_expression,
                node_having_prerequisites=node_having_prerequisites.entity_id,
                context_tree=context_tree.entity_id
            )
            new_prerequisite.has_changed = True
            if new_prerequisite in self.prerequisites:
                self.prerequisites.remove(new_prerequisite)
            self.prerequisites.append(new_prerequisite)
        return messages

    @staticmethod
    def __clean_set_prerequisite(
            prerequisite_expression: 'PrerequisiteExpression',
            node: 'NodeLearningUnitYear',
            context_tree: 'ProgramTree'
    ) -> (bool, List['BusinessValidationMessage']):
        validator = validators_by_business_action.UpdatePrerequisiteValidatorList(
            prerequisite_expression,
            node,
            context_tree
        )
        return validator.is_valid(), validator.messages

    @cached_result
    def __map_is_prerequisite_of(self) -> Dict['NodeIdentity', List['NodeIdentity']]:
        from program_management.ddd.domain.service.identity_search import NodeIdentitySearch
        result = {}
        for prerequisite in self.prerequisites:
            node_having_prerequisites = prerequisite.node_having_prerequisites
            for prereq_item in prerequisite.get_all_prerequisite_items():
                prereq_item_as_node_identity = NodeIdentitySearch().get_from_prerequisite_item(prereq_item)
                result.setdefault(prereq_item_as_node_identity, set()).add(node_having_prerequisites)
        result = {
            node_is_prerequisite: sorted(nodes_having_prerequisites, key=lambda node_identity: node_identity.code)
            for node_is_prerequisite, nodes_having_prerequisites in result.items()
        }
        return result

    @cached_result
    def _map_node_identity_prerequisite(self) -> Dict['NodeIdentity', 'Prerequisite']:
        return {p.node_having_prerequisites: p for p in self.prerequisites}


@attr.s(slots=True)
class NullPrerequisites(Prerequisites):
    context_tree = attr.ib(type='ProgramTreeIdentity', default=None)

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
import functools
from typing import Callable, List, Set

from osis_common.ddd import interface
from program_management.ddd.business_types import *
from base.models.education_group_year import EducationGroupYear
from education_group.models.group_year import GroupYear

STANDARD = ""


class ProgramTreeVersionAttributes:
    def __init__(
            self,
            version_name: str = STANDARD,
            is_transition: bool = False,
            title_fr: str = None,
            title_en: str = None,
    ):
        self.version_name = version_name or STANDARD
        self.is_transition = is_transition
        self.title_fr = title_fr
        self.title_en = title_en


NodesToCopy = List['Node']
SearchYear = int
ExistingNodesWithTheirChildren = List['Node']


# FIXME :: same identity than NodeIdentity and ProgramTreeIdentity
class ProgramTreeVersionIdentity(interface.EntityIdentity):
    def __init__(self, code: str, year: int):
        self.code = code
        self.year = year

    def __hash__(self):
        return hash(self.code + str(self.year))

    def __eq__(self, other):
        return self.code == other.code and self.year == other.year


class ProgramTreeVersionFromAnotherTreeBuilder:

    def __init__(
            self,
            from_tree: 'ProgramTreeVersion',
            tree_to_fill: 'ProgramTreeVersion',
            node_repository: 'NodeRepository',  # Dependency injection
    ):
        # TODO :: validators to use :
        # TODO :: MinimumMaximumPostponementYearValidator
        # TODO :: EndYearPostponementValidator
        # TODO :: HasContentToPostponeValidator
        # TODO :: ProgramTreeAlreadyPostponedValidator
        # validator = validate()
        # if not validator.is_Valid():
        #     return validator.messages
        self.from_tree = from_tree
        self.tree_to_fill = tree_to_fill
        self.node_repository = node_repository

    @property
    def copy_from_year(self) -> int:
        return self.from_tree.tree.root_node.year

    @property
    def copy_to_year(self) -> int:
        return self.copy_from_year + 1

    @property
    def nodes_to_copy(self) -> Set['Node']:
        return self.from_tree.tree.get_all_nodes()

    @property
    @functools.lru_cache()
    def existing_nodes_in_destination_year(self) -> ExistingNodesWithTheirChildren:
        return self.node_repository.search_nodes_next_year(
                list(n.pk for n in self.nodes_to_copy),
                self.copy_to_year
            )

    def build(self) -> 'ProgramTreeVersion':
        if self.from_tree.is_transition:
            tree_version = self._build_from_transition()
        else:
            tree_version = self._build_from_standard()
        return tree_version

    def _build_from_transition(self) -> 'ProgramTreeVersion':
        raise NotImplementedError()

    def _build_from_standard(self) -> 'ProgramTreeVersion':
        raise NotImplementedError()


class ProgramTreeVersion(interface.RootEntity):

    def __init__(
            self,
            tree: 'ProgramTree',
            version_name: str = STANDARD,
            is_transition: bool = False,
            offer: int = None,
            title_fr: str = None,
            title_en: str = None,
            root_group = None
    ):
        super(ProgramTreeVersion, self).__init__()
        self.tree = tree  # FIXME :: replace this param with "root_code" and "year"
        self.is_transition = is_transition
        self.version_name = version_name
        self.offer = offer
        self.title_fr = title_fr
        self.title_en = title_en
        self.root_group = root_group

    @property
    def entity_id(self) -> ProgramTreeVersionIdentity:  # FIXME :: pass entity_id into the constructor
        return ProgramTreeVersionIdentity(self.tree.root_node.code, self.tree.root_node.year)

    @property
    def is_standard(self):
        return self.version_name == STANDARD

    @property
    def version_label(self):
        if self.is_standard:
            return 'Transition' if self.is_transition else ''
        else:
            return '{}-Transition'.format(self.version_name) if self.is_transition else self.version_name


class ProgramTreeVersionNotFoundException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("The program version cannot be found")

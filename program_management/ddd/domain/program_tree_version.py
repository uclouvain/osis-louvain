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
from osis_common.ddd import interface
from program_management.ddd.business_types import *

STANDARD = ""


class ProgramTreeVersionBuilder:

    _tree_version = None

    def build_from(self, from_tree: 'ProgramTreeVersion', **tree_version_attrs) -> 'ProgramTreeVersion':
        assert isinstance(from_tree, ProgramTreeVersion)
        assert from_tree.is_standard, "Forbidden to copy from a non Standard version"
        if from_tree.is_transition:
            self._tree_version = self._build_from_transition(from_tree.tree, **tree_version_attrs)
        else:
            self._tree_version = self._build_from_standard(from_tree.tree, **tree_version_attrs)
        return self.program_tree_version

    @property
    def program_tree_version(self):
        return self._tree_version

    def _build_from_transition(self, from_tree: 'ProgramTree', **tree_version_attrs) -> 'ProgramTreeVersion':
        raise NotImplementedError()

    def _build_from_standard(self, from_tree: 'ProgramTree', **tree_version_attrs) -> 'ProgramTreeVersion':
        raise NotImplementedError()


class ProgramTreeVersion(interface.RootEntity):

    def __init__(
            self,
            entity_identity: 'ProgramTreeVersionIdentity',
    ):
        super(ProgramTreeVersion, self).__init__(entity_id=entity_identity)
        self.entity_id = entity_identity

    @property
    def is_standard(self):
        return self.entity_id.version_name == STANDARD

    @property
    def is_transition(self) -> bool:
        return self.entity_id.is_transition

    @property
    def version_name(self) -> str:
        return self.entity_id.version_name


class ProgramTreeVersionIdentity(interface.EntityIdentity):
    def __init__(self, offer_acronym: str, year: int, version_name: str, is_transition: bool):
        self.offer_acronym = offer_acronym
        self.year = year
        self.version_name = version_name
        self.is_transition = is_transition

    def __hash__(self):
        return hash(str(self.offer_acronym) + str(self.year) + str(self.version_name) + str(self.is_transition))

    def __eq__(self, other):
        return self.offer_acronym == other.offer_acronym \
               and self.year == other.year \
               and self.version_name == other.version_name \
               and self.is_transition == other.is_transition

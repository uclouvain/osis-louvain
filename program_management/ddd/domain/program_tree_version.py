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
import attr

from osis_common.ddd import interface
from program_management.ddd.business_types import *
import attr
from program_management.ddd.command import CreateStandardVersionCommand
from program_management.ddd.domain.program_tree import ProgramTreeIdentity, ProgramTree

STANDARD = ""


@attr.s(frozen=True, slots=True)
class ProgramTreeVersionIdentity(interface.EntityIdentity):
    offer_acronym = attr.ib(type=str)
    year = attr.ib(type=int)
    version_name = attr.ib(type=str)
    is_transition = attr.ib(type=bool)


class ProgramTreeVersionBuilder:

    _tree_version = None

    def copy_to_next_year(
            self,
            copy_from: 'ProgramTreeVersion',
            tree_version_repository: 'ProgramTreeVersionRepository'
    ) -> 'ProgramTreeVersion':
        identity_next_year = attr.evolve(copy_from.entity_id, year=copy_from.entity_id.year + 1)
        tree_version_next_year = tree_version_repository.get(identity_next_year)
        if tree_version_next_year:
            # Case update program tree version to next year
            # TODO :: To implement in OSIS-4386
            pass
        else:
            # Case create program tree version to next year
            tree_version_next_year = attr.evolve(  # Copy to new object
                copy_from,
                entity_identity=identity_next_year,
                entity_id=identity_next_year,
                program_tree_identity=attr.evolve(
                    copy_from.program_tree_identity,
                    year=copy_from.program_tree_identity.year + 1
                ),
            )
        return tree_version_next_year

    def build_standard_version(
            self,
            cmd: CreateStandardVersionCommand,
            tree_repository: 'ProgramTreeRepository'
    ) -> 'ProgramTreeVersion':
        tree_version_identity = ProgramTreeVersionIdentity(
            offer_acronym=cmd.offer_acronym,
            year=cmd.year,
            version_name=STANDARD,
            is_transition=False,
        )
        tree_identity = ProgramTreeIdentity(code=cmd.code, year=cmd.year)
        return ProgramTreeVersion(
            entity_identity=tree_version_identity,
            entity_id=tree_version_identity,
            program_tree_identity=tree_identity,
            program_tree_repository=tree_repository,
            title_fr=None,
            title_en=None,
        )

    def build_from(self, from_tree: 'ProgramTreeVersion', **tree_version_attrs) -> 'ProgramTreeVersion':
        assert isinstance(from_tree, ProgramTreeVersion)
        assert from_tree.is_standard, "Forbidden to copy from a non Standard version"
        if from_tree.is_transition:
            self._tree_version = self._build_from_transition(from_tree.get_tree(), **tree_version_attrs)
        else:
            self._tree_version = self._build_from_standard(from_tree.get_tree(), **tree_version_attrs)
        return self.program_tree_version

    @property
    def program_tree_version(self):
        return self._tree_version

    def _build_from_transition(self, from_tree: 'ProgramTree', **tree_version_attrs) -> 'ProgramTreeVersion':
        raise NotImplementedError()

    def _build_from_standard(self, from_tree: 'ProgramTree', **tree_version_attrs) -> 'ProgramTreeVersion':
        raise NotImplementedError()


# FIXME :: should be in a separate DDD domain
@attr.s(slots=True)
class ProgramTreeVersion(interface.RootEntity):

    entity_identity = entity_id = attr.ib(type=ProgramTreeVersionIdentity)
    program_tree_identity = attr.ib(type=ProgramTreeIdentity)
    program_tree_repository = attr.ib(type=interface.AbstractRepository)
    title_fr = attr.ib(type=str, default=None)
    title_en = attr.ib(type=str, default=None)
    tree = attr.ib(type=ProgramTree, default=None)

    _tree = None

    def get_tree(self) -> 'ProgramTree':
        if not self._tree:
            self._tree = self.program_tree_repository.get(self.program_tree_identity)
        return self._tree

    @property
    def is_standard(self):
        return self.entity_id.version_name == STANDARD

    @property
    def is_transition(self) -> bool:
        return self.entity_id.is_transition

    @property
    def version_name(self) -> str:
        return self.entity_id.version_name

    @property
    def version_label(self):  # TODO :: to remove
        if self.is_standard:
            return '[Transition]' if self.is_transition else ''
        else:
            return '[{}-Transition]'.format(
                self.version_name
            ) if self.is_transition else '[{}]'.format(self.version_name)

    @property
    def is_standard_version(self):
        return self.entity_id.version_name == STANDARD and not self.entity_id.is_transition


class ProgramTreeVersionNotFoundException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__("The program version cannot be found")

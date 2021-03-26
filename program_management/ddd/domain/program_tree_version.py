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
from typing import Union, Set

import attr

from base.ddd.utils.converters import to_upper_case_converter
from osis_common.ddd import interface
from program_management.ddd.business_types import *
from program_management.ddd.command import CreateProgramTreeSpecificVersionCommand, \
    CreateProgramTreeTransitionVersionCommand, CreateStandardVersionCommand
from program_management.ddd.domain import exception, academic_year
from program_management.ddd.domain import program_tree
from program_management.ddd.validators import validators_by_business_action

STANDARD = ""
NOT_A_TRANSITION = ""
TRANSITION_PREFIX = "TRANSITION"


@attr.s(frozen=True, slots=True)
class ProgramTreeVersionIdentity(interface.EntityIdentity):
    offer_acronym = attr.ib(type=str, converter=to_upper_case_converter)
    year = attr.ib(type=int)
    version_name = attr.ib(type=str, converter=to_upper_case_converter)
    transition_name = attr.ib(type=str, converter=to_upper_case_converter, default=NOT_A_TRANSITION)

    @property
    def is_standard(self) -> bool:
        return self.version_name == STANDARD or self.version_name is None

    @property
    def is_official_standard(self) -> bool:
        return self.is_standard and not self.is_transition

    @property
    def is_standard_transition(self) -> bool:
        return self.is_standard and self.is_transition

    @property
    def is_specific_transition(self) -> bool:
        return not self.is_standard and self.is_transition

    @property
    def is_specific_official(self) -> bool:
        return not self.is_standard and not self.is_transition

    @property
    def is_transition(self) -> bool:
        return bool(self.transition_name)


class ProgramTreeVersionBuilder:
    _tree_version = None

    def fill_from_program_tree_version(
            self,
            from_tree_version: 'ProgramTreeVersion',
            to_tree_version: 'ProgramTreeVersion',
            existing_learning_unit_nodes: Set['NodeLearningUnitYear'],
            existing_trees: Set['ProgramTree']
    ) -> 'ProgramTreeVersion':
        validators_by_business_action.FillProgramTreeVersionValidatorList(from_tree_version, to_tree_version).validate()
        program_tree.ProgramTreeBuilder().fill_from_program_tree(
                from_tree_version.get_tree(),
                to_tree_version.get_tree(),
                existing_learning_unit_nodes,
                existing_trees
            )
        return to_tree_version

    def copy_to_next_year(
            self,
            copy_from: 'ProgramTreeVersion',
            tree_version_repository: 'ProgramTreeVersionRepository'
    ) -> 'ProgramTreeVersion':
        validators_by_business_action.CopyProgramTreeVersionValidatorList(copy_from).validate()
        identity_next_year = attr.evolve(copy_from.entity_id, year=copy_from.entity_id.year + 1)
        try:
            tree_version_next_year = tree_version_repository.get(identity_next_year)
            tree_version_next_year.update(
                UpdateProgramTreeVersiongData(
                    title_fr=copy_from.title_fr,
                    title_en=copy_from.title_en,
                    end_year_of_existence=copy_from.end_year_of_existence,
                )
            )
        except exception.ProgramTreeVersionNotFoundException:
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
            year=cmd.start_year,
            version_name=STANDARD,
            transition_name=NOT_A_TRANSITION,
        )
        tree_identity = program_tree.ProgramTreeIdentity(code=cmd.code, year=cmd.start_year)
        return ProgramTreeVersion(
            entity_identity=tree_version_identity,
            entity_id=tree_version_identity,
            program_tree_identity=tree_identity,
            program_tree_repository=tree_repository,
            start_year=cmd.start_year,
            title_fr=None,
            title_en=None,
        )

    def create_from_existing_version(
            self,
            from_existing_version: 'ProgramTreeVersion',
            new_tree_identity: 'ProgramTreeIdentity',
            command: Union['CreateProgramTreeSpecificVersionCommand', 'CreateProgramTreeTransitionVersionCommand'],
    ) -> 'ProgramTreeVersion':
        if command.transition_name:
            validator = validators_by_business_action.CreateProgramTreeTransitionVersionValidatorList(
                command.start_year,
                command.offer_acronym,
                command.version_name,
                command.transition_name
            )
        else:
            validator = validators_by_business_action.CreateProgramTreeVersionValidatorList(
                command.start_year,
                command.offer_acronym,
                command.version_name,
                command.transition_name
            )
        if validator.is_valid():
            assert isinstance(from_existing_version, ProgramTreeVersion)
            assert not from_existing_version.is_transition, "Forbidden to create a version from a transition"
            assert not (from_existing_version.version_name and command.version_name and not command.transition_name), \
                "Forbidden to create a specific version from an other specific version"
            self._tree_version = self._build_from_existing(
                from_existing_version,
                new_tree_identity,
                command,
            )
            return self.program_tree_version

    @property
    def program_tree_version(self):
        return self._tree_version

    def _build_from_existing(
            self,
            from_tree_version: 'ProgramTreeVersion',
            new_tree_identity: 'ProgramTreeIdentity',
            command: Union['CreateProgramTreeSpecificVersionCommand', 'CreateProgramTreeTransitionVersionCommand'],
    ) -> 'ProgramTreeVersion':
        tree_version_identity = ProgramTreeVersionIdentity(
            offer_acronym=from_tree_version.entity_id.offer_acronym,
            version_name=command.version_name,
            year=from_tree_version.entity_id.year,
            transition_name=command.transition_name
        )
        return ProgramTreeVersion(
            program_tree_identity=new_tree_identity,
            program_tree_repository=from_tree_version.program_tree_repository,
            start_year=command.start_year,
            entity_identity=tree_version_identity,
            entity_id=tree_version_identity,
            title_en=command.title_en,
            title_fr=command.title_fr,
            end_year_of_existence=command.end_year,
        )


@attr.s(frozen=True, slots=True, kw_only=True)
class UpdateProgramTreeVersiongData:
    title_fr = attr.ib(type=str, default="")
    title_en = attr.ib(type=str, default="")
    end_year_of_existence = attr.ib(type=int, default=None)


# FIXME :: should be in a separate DDD domain
@attr.s(slots=True)
class ProgramTreeVersion(interface.RootEntity):
    entity_identity = entity_id = attr.ib(type=ProgramTreeVersionIdentity)
    program_tree_identity = attr.ib(type='ProgramTreeIdentity')
    program_tree_repository = attr.ib(type=interface.AbstractRepository)
    start_year = attr.ib(type=int)
    transition_name = attr.ib(type=str)
    version_name = attr.ib(type=str)
    title_fr = attr.ib(type=str, default=None)
    title_en = attr.ib(type=str, default=None)
    tree = attr.ib(type='ProgramTree', default=None)
    end_year_of_existence = attr.ib(type=int, default=None)

    def get_tree(self) -> 'ProgramTree':
        if not self.tree:
            self.tree = self.program_tree_repository.get(self.program_tree_identity)
        return self.tree

    @property
    def is_standard(self):
        return self.entity_id.is_standard

    @property
    def end_year(self):
        return academic_year.AcademicYear(year=self.end_year_of_existence)

    @property
    def is_transition(self) -> bool:
        return self.entity_id.is_transition

    @transition_name.default
    def _transition_name(self) -> str:
        return self.entity_id.transition_name

    @version_name.default
    def _version_name(self) -> str:
        return self.entity_id.version_name

    @property
    def is_official_standard(self) -> bool:
        return self.entity_id.is_official_standard

    @property
    def is_specific_official(self) -> bool:
        return self.entity_id.is_specific_official

    @property
    def is_specific_transition(self) -> bool:
        return self.entity_id.is_specific_transition

    @property
    def is_standard_transition(self) -> bool:
        return self.entity_id.is_standard_transition

    def update(self, data: UpdateProgramTreeVersiongData) -> 'ProgramTreeVersion':
        data_as_dict = attr.asdict(data, recurse=False)
        for field, new_value in data_as_dict.items():
            setattr(self, field, new_value)
        validators_by_business_action.UpdateProgramTreeVersionValidatorList(self).validate()
        return self


# FIXME :: à discuter de la manière de faire à cause de code presque dupliqué
def version_label(entity_id: 'ProgramTreeVersionIdentity', only_label: bool = False):
    if not entity_id.is_official_standard:
        if entity_id.is_standard_transition:
            label = '[{}]'.format(entity_id.transition_name)
        elif entity_id.is_specific_official:
            label = '[{}]'.format(entity_id.version_name)
        else:
            label = '[{}-{}]'.format(entity_id.version_name, entity_id.transition_name)
        return label[1:len(label) - 1] if only_label else label
    return ''

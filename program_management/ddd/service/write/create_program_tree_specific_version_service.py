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
from program_management.ddd.command import CreateProgramTreeSpecificVersionCommand, DuplicateProgramTree
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionBuilder, ProgramTreeVersionIdentity, \
    STANDARD, NOT_A_TRANSITION
from program_management.ddd.repositories import program_tree_version as tree_version_repo
from program_management.ddd.service.write import duplicate_program_tree_service


def create_program_tree_specific_version(
        command: 'CreateProgramTreeSpecificVersionCommand'
) -> ProgramTreeVersionIdentity:

    # GIVEN
    tree_version_identity_from = ProgramTreeVersionIdentity(
        offer_acronym=command.offer_acronym,
        year=command.start_year,
        version_name=STANDARD,
        transition_name=NOT_A_TRANSITION
    )
    repo = tree_version_repo.ProgramTreeVersionRepository()
    program_tree_version_from = repo.get(entity_id=tree_version_identity_from)

    # WHEN
    new_program_tree_identity = duplicate_program_tree_service.create_and_fill_from_existing_tree(
        DuplicateProgramTree(
            from_root_code=program_tree_version_from.program_tree_identity.code,
            from_root_year=program_tree_version_from.program_tree_identity.year,
            duplicate_to_transition=command.transition_name,
            override_end_year_to=command.end_year,
            override_start_year_to=command.start_year,
        )
    )
    new_program_tree_version = ProgramTreeVersionBuilder().create_from_existing_version(
        program_tree_version_from,
        new_program_tree_identity,
        command,
    )

    # THEN
    identity = repo.create(
        program_tree_version=new_program_tree_version,
    )

    return identity

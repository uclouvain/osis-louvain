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
from program_management.ddd.command import CreateProgramTreeVersionCommand, DuplicateProgramTree
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionBuilder, ProgramTreeVersionIdentity, \
    STANDARD
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.write import duplicate_program_tree_service


def create_program_tree_version(
        command: 'CreateProgramTreeVersionCommand',
) -> ProgramTreeVersionIdentity:

    # GIVEN
    identity_standard = ProgramTreeVersionIdentity(
        offer_acronym=command.offer_acronym,
        year=command.start_year,
        version_name=STANDARD,
        is_transition=False
    )
    program_tree_version_standard = ProgramTreeVersionRepository().get(entity_id=identity_standard)

    # WHEN
    new_program_tree_identity = duplicate_program_tree_service.duplicate_program_tree(
        DuplicateProgramTree(
            from_root_code=program_tree_version_standard.program_tree_identity.code,
            from_root_year=program_tree_version_standard.program_tree_identity.year,
            override_end_year_to=command.end_year,
            override_start_year_to=command.start_year
        )
    )
    new_program_tree_version = ProgramTreeVersionBuilder().create_from_standard_version(
        program_tree_version_standard,
        new_program_tree_identity,
        command,
    )

    # THEN
    identity = ProgramTreeVersionRepository.create(
        program_tree_version=new_program_tree_version,
    )

    return identity

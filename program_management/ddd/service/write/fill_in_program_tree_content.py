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
from osis_common.ddd.interface import EntityIdentity
from program_management.ddd.command import FillInProgramTreeContentCommand
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionFromAnotherTreeBuilder, \
    ProgramTreeVersionIdentity
from program_management.ddd.repositories.node import NodeRepository
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository


def fill_in_program_tree_content(command: FillInProgramTreeContentCommand) -> EntityIdentity:
    # Given
    fill_in_from_tree = ProgramTreeVersionRepository.get(
        ProgramTreeVersionIdentity(
            command.from_root_node_code,
            command.from_root_node_year,
        )
    )

    tree_to_fill = ProgramTreeVersionRepository.get(
        ProgramTreeVersionIdentity(
            command.to_root_node_code,
            command.to_root_node_year,
        )
    )

    # When
    new_version = ProgramTreeVersionFromAnotherTreeBuilder(
        fill_in_from_tree,
        tree_to_fill,
        NodeRepository(),
    ).build()

    # Then
    identity = ProgramTreeVersionRepository.create(new_version)

    return identity

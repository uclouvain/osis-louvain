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
from django.db import transaction

from program_management.ddd.command import UpdateProgramTreeVersionCommand, DeleteSpecificVersionCommand
from program_management.ddd.domain import exception
from program_management.ddd.domain.program_tree_version import UpdateProgramTreeVersiongData, \
    ProgramTreeVersionIdentity, ProgramTreeVersion
from program_management.ddd.domain.service.calculate_end_postponement import CalculateEndPostponement
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.write import delete_specific_version_service


@transaction.atomic()
def update_program_tree_version(
        command: 'UpdateProgramTreeVersionCommand',
) -> 'ProgramTreeVersionIdentity':
    identity = ProgramTreeVersionIdentity(
        offer_acronym=command.offer_acronym,
        year=command.year,
        version_name=command.version_name,
        transition_name=command.transition_name,
    )
    repository = ProgramTreeVersionRepository()
    program_tree_version = repository.get(entity_id=identity)

    __call_delete_service(program_tree_version, command.end_year)

    program_tree_version.update(__convert_command_to_update_data(command))

    identity = repository.update(
        program_tree_version,
    )

    return identity


def __convert_command_to_update_data(cmd: UpdateProgramTreeVersionCommand) -> 'UpdateProgramTreeVersiongData':
    return UpdateProgramTreeVersiongData(
        title_fr=cmd.title_fr,
        title_en=cmd.title_en,
        end_year_of_existence=cmd.end_year,
    )


def __call_delete_service(program_tree_version: 'ProgramTreeVersion', end_year_updated: int):
    identity = program_tree_version.entity_identity

    postponement_limit = CalculateEndPostponement.calculate_end_postponement_limit()

    end_year = program_tree_version.end_year_of_existence or postponement_limit
    end_year_updated = end_year_updated or postponement_limit

    if end_year > end_year_updated:
        limit = (program_tree_version.end_year_of_existence or postponement_limit) + 1
        for year_to_delete in range(end_year_updated + 1, limit):
            try:
                delete_specific_version_service.delete_specific_version(
                    DeleteSpecificVersionCommand(
                        acronym=identity.offer_acronym,
                        year=year_to_delete,
                        version_name=identity.version_name,
                        transition_name=identity.transition_name,
                    )
                )
            except exception.ProgramTreeVersionNotFoundException:
                continue

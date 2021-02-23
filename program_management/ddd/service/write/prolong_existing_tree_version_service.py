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
from typing import List

from django.db import transaction

from program_management.ddd.command import PostponeProgramTreeVersionCommand, ExtendProgramTreeVersionCommand, \
    ProlongExistingProgramTreeVersionCommand, UpdateProgramTreeVersionCommand
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity
from program_management.ddd.domain.service.identity_search import GroupIdentitySearch
from program_management.ddd.service.write import extend_existing_tree_version_service, \
    update_program_tree_version_service, postpone_tree_specific_version_service


@transaction.atomic()
def prolong_existing_tree_version(
        command: 'ProlongExistingProgramTreeVersionCommand'
) -> List['ProgramTreeVersionIdentity']:
    identities = extend_existing_tree_version_service.extend_existing_past_version(
        __convert_to_extend_command(command)
    )
    update_program_tree_version_service.update_program_tree_version(
        __convert_to_update_command(command)
    )
    postpone_tree_specific_version_service.postpone_program_tree_version(
        __convert_to_postpone_command(command)
    )
    return identities


def __convert_to_extend_command(command: ProlongExistingProgramTreeVersionCommand) -> ExtendProgramTreeVersionCommand:
    return ExtendProgramTreeVersionCommand(
        end_year_of_existence=command.end_year,
        offer_acronym=command.offer_acronym,
        version_name=command.version_name,
        year=command.updated_year,
        transition_name=command.transition_name
    )


def __convert_to_update_command(command: ProlongExistingProgramTreeVersionCommand) -> UpdateProgramTreeVersionCommand:
    return UpdateProgramTreeVersionCommand(
        offer_acronym=command.offer_acronym,
        version_name=command.version_name,
        year=command.updated_year,
        transition_name=command.transition_name,
        title_en=command.title_en,
        title_fr=command.title_fr,
        end_year=command.end_year,
    )


def __convert_to_postpone_command(
        command: ProlongExistingProgramTreeVersionCommand
) -> PostponeProgramTreeVersionCommand:
    group_identity = GroupIdentitySearch().get_from_tree_version_identity(
        ProgramTreeVersionIdentity(
            offer_acronym=command.offer_acronym,
            year=command.updated_year,
            version_name=command.version_name,
            transition_name=command.transition_name,
        )
    )
    return PostponeProgramTreeVersionCommand(
        from_offer_acronym=command.offer_acronym,
        from_version_name=command.version_name,
        from_year=command.updated_year,
        from_transition_name=command.transition_name,
        from_code=group_identity.code,
    )

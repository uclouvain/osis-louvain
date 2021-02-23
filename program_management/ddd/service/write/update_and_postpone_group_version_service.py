# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from typing import List

from education_group.ddd import command as education_group_command
from education_group.ddd.domain.exception import GroupCopyConsistencyException, TrainingNotFoundException
from education_group.ddd.domain.service.conflicted_fields import ConflictedFields
from education_group.ddd.service.read import get_group_service
from education_group.ddd.service.write import copy_group_service, update_group_service
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.command import CopyTreeVersionToNextYearCommand
from program_management.ddd.domain import exception
from program_management.ddd.domain.service.calculate_end_postponement import CalculateEndPostponement
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.write import copy_program_version_service


def update_and_postpone_group_version(
        postpone_cmd: command.PostponeGroupVersionCommand
) -> List['ProgramTreeVersionIdentity']:
    from_year = postpone_cmd.postpone_from_year

    cmd_get = education_group_command.GetGroupCommand(code=postpone_cmd.code, year=from_year)
    group = get_group_service.get_group(cmd_get)

    conflicted_fields = ConflictedFields().get_group_conflicted_fields(group.entity_id)
    update_group_service.update_group(
        education_group_command.UpdateGroupCommand(
            code=postpone_cmd.code,
            year=postpone_cmd.postpone_from_year,
            abbreviated_title=postpone_cmd.abbreviated_title,
            title_fr=postpone_cmd.title_fr,
            title_en=postpone_cmd.title_en,
            credits=postpone_cmd.credits,
            constraint_type=postpone_cmd.constraint_type,
            min_constraint=postpone_cmd.min_constraint,
            max_constraint=postpone_cmd.max_constraint,
            management_entity_acronym=postpone_cmd.management_entity_acronym,
            teaching_campus_name=postpone_cmd.teaching_campus_name,
            organization_name=postpone_cmd.organization_name,
            remark_fr=postpone_cmd.remark_fr,
            remark_en=postpone_cmd.remark_en,
            end_year=postpone_cmd.end_year,
        )
    )

    identities_created = []
    end_postponement_year = CalculateEndPostponement.calculate_end_postponement_year_group(
        identity=group.entity_identity,
        repository=ProgramTreeVersionRepository(),
    )
    for year in range(from_year, end_postponement_year):
        try:
            if year + 1 in conflicted_fields:
                continue  # Do not copy info from year to N+1 because conflict detected

            copy_group_service.copy_group(
                cmd=education_group_command.CopyGroupCommand(from_code=postpone_cmd.code, from_year=year)
            )

            cmd_copy_from = CopyTreeVersionToNextYearCommand(
                from_offer_acronym=postpone_cmd.from_offer_acronym,
                from_year=year,
                from_version_name=postpone_cmd.from_version_name,
                from_transition_name=postpone_cmd.from_transition_name,
                from_offer_code=postpone_cmd.code
            )
            identity_next_year = copy_program_version_service.copy_tree_version_to_next_year(cmd_copy_from)
            identities_created.append(identity_next_year)

        #  FIXME Do the postponement until the standard version existence in reposotory
        except (exception.CannotCopyTreeVersionDueToEndDate, TrainingNotFoundException):
            break

    if conflicted_fields:
        first_conflict_year = min(conflicted_fields.keys())
        raise GroupCopyConsistencyException(first_conflict_year, conflicted_fields[first_conflict_year])
    return identities_created

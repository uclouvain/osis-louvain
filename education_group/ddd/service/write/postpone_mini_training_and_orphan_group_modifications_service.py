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

from education_group.ddd import command
from education_group.ddd.domain.exception import MiniTrainingCopyConsistencyException
from education_group.ddd.domain.mini_training import MiniTrainingIdentity
from education_group.ddd.domain.service.conflicted_fields import ConflictedFields
from education_group.ddd.repository import mini_training as mini_training_repository
from education_group.ddd.service.write import copy_mini_training_service, update_mini_training_and_group_service, \
    copy_group_service
from program_management.ddd.domain.service.calculate_end_postponement import CalculateEndPostponement


def postpone_mini_training_and_orphan_group_modifications(
        postpone_cmd: command.PostponeMiniTrainingAndGroupModificationCommand
) -> List['MiniTrainingIdentity']:

    # GIVEN
    from_year = postpone_cmd.postpone_from_year
    from_mini_training_id = MiniTrainingIdentity(acronym=postpone_cmd.postpone_from_abbreviated_title, year=from_year)
    conflicted_fields = ConflictedFields().get_mini_training_conflicted_fields(from_mini_training_id)

    # WHEN
    identities_created = [
        update_mini_training_and_group_service.update_mini_training_and_group(
            command.UpdateMiniTrainingAndGroupCommand(
                abbreviated_title=postpone_cmd.postpone_from_abbreviated_title,
                code=postpone_cmd.code,
                year=postpone_cmd.postpone_from_year,
                status=postpone_cmd.status,
                credits=postpone_cmd.credits,
                title_fr=postpone_cmd.title_fr,
                title_en=postpone_cmd.title_en,
                keywords=postpone_cmd.keywords,
                management_entity_acronym=postpone_cmd.management_entity_acronym,
                end_year=postpone_cmd.end_year,
                teaching_campus_name=postpone_cmd.teaching_campus_name,
                constraint_type=postpone_cmd.constraint_type,
                min_constraint=postpone_cmd.min_constraint,
                max_constraint=postpone_cmd.max_constraint,
                remark_fr=postpone_cmd.remark_fr,
                remark_en=postpone_cmd.remark_en,
                organization_name=postpone_cmd.organization_name,
                schedule_type=postpone_cmd.schedule_type,
            )
        )
    ]
    end_postponement_year = CalculateEndPostponement.calculate_end_postponement_year_mini_training(
        identity=from_mini_training_id,
        repository=mini_training_repository.MiniTrainingRepository()
    )

    for year in range(from_year, end_postponement_year):
        if year + 1 in conflicted_fields:
            continue  # Do not copy info from year to N+1 because conflict detected

        identity_next_year = copy_mini_training_service.copy_mini_training_to_next_year(
            copy_cmd=command.CopyMiniTrainingToNextYearCommand(
                acronym=postpone_cmd.postpone_from_abbreviated_title,
                postpone_from_year=year
            )
        )
        copy_group_service.copy_group(
            cmd=command.CopyGroupCommand(
                from_code=postpone_cmd.code,
                from_year=year
            )
        )

        # THEN
        identities_created.append(identity_next_year)

    if conflicted_fields:
        first_conflict_year = min(conflicted_fields.keys())
        raise MiniTrainingCopyConsistencyException(first_conflict_year, conflicted_fields[first_conflict_year])
    return identities_created

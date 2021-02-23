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
from education_group.ddd.business_types import *
from education_group.ddd.domain.exception import MiniTrainingCopyConsistencyException
from education_group.ddd.service.write import postpone_mini_training_and_orphan_group_modifications_service
from program_management.ddd import command as pgm_cmd
from program_management.ddd.service.write import postpone_tree_specific_version_service, \
    postpone_program_tree_service, update_program_tree_version_end_date_service
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION, STANDARD


def postpone_mini_training_and_program_tree_modifications(
        update_command: pgm_cmd.PostponeMiniTrainingAndRootGroupModificationWithProgramTreeCommand
) -> List['MiniTrainingIdentity']:
    update_program_tree_version_end_date_service.update_program_tree_version_end_date(
        __convert_to_update_program_tree_version_end_date_command(update_command)
    )

    consistency_error = None
    try:
        mini_training_identities = postpone_mini_training_and_orphan_group_modifications_service.\
            postpone_mini_training_and_orphan_group_modifications(
                __convert_to_postpone_mini_training_and_group_modification_command(update_command)
            )
    except MiniTrainingCopyConsistencyException as e:
        consistency_error = e

    postpone_program_tree_service.postpone_program_tree(
        pgm_cmd.PostponeProgramTreeCommand(
            from_code=update_command.code,
            from_year=update_command.year,
            offer_acronym=update_command.abbreviated_title,
        )
    )

    postpone_tree_specific_version_service.postpone_program_tree_version(
        pgm_cmd.PostponeProgramTreeVersionCommand(
            from_offer_acronym=update_command.abbreviated_title,
            from_version_name=STANDARD,
            from_year=update_command.year,
            from_transition_name=NOT_A_TRANSITION,
        )
    )
    if consistency_error:
        raise consistency_error
    return mini_training_identities


def __convert_to_postpone_mini_training_and_group_modification_command(
        mini_training_cmd: pgm_cmd.PostponeMiniTrainingAndRootGroupModificationWithProgramTreeCommand
) -> command.PostponeMiniTrainingAndGroupModificationCommand:
    return command.PostponeMiniTrainingAndGroupModificationCommand(
        code=mini_training_cmd.code,
        postpone_from_year=mini_training_cmd.year,
        postpone_from_abbreviated_title=mini_training_cmd.abbreviated_title,
        title_fr=mini_training_cmd.title_fr,
        title_en=mini_training_cmd.title_en,
        credits=mini_training_cmd.credits,
        management_entity_acronym=mini_training_cmd.management_entity_acronym,
        organization_name=mini_training_cmd.teaching_campus_organization_name,
        end_year=mini_training_cmd.end_year,
        keywords=mini_training_cmd.keywords,
        schedule_type=mini_training_cmd.schedule_type,
        status=mini_training_cmd.status,
        teaching_campus_name=mini_training_cmd.teaching_campus_name,
        constraint_type=mini_training_cmd.constraint_type,
        min_constraint=mini_training_cmd.min_constraint,
        max_constraint=mini_training_cmd.max_constraint,
        remark_fr=mini_training_cmd.remark_fr,
        remark_en=mini_training_cmd.remark_en,
    )


def __convert_to_update_program_tree_version_end_date_command(
        cmd: pgm_cmd.PostponeMiniTrainingAndRootGroupModificationWithProgramTreeCommand
) -> pgm_cmd.UpdateProgramTreeVersionEndDateCommand:
    return pgm_cmd.UpdateProgramTreeVersionEndDateCommand(
        from_offer_acronym=cmd.abbreviated_title,
        from_version_name="",
        from_year=cmd.year,
        from_transition_name=NOT_A_TRANSITION,
        end_date=cmd.end_year
    )

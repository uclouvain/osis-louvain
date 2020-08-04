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

from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.service.write import create_group_service, create_orphan_training_service
from program_management.ddd.command import CreateStandardVersionCommand, PostponeProgramTreeVersionCommand, \
    PostponeProgramTreeCommand
from program_management.ddd.service.write import create_standard_version_service, postpone_tree_version_service, \
    create_standard_program_tree_service, postpone_program_tree_service


@transaction.atomic()
def create_and_report_training_with_program_tree(
        create_training_cmd: command.CreateTrainingCommand
) -> List['TrainingIdentity']:
    # GIVEN
    cmd = create_training_cmd

    # WHEN
    training_identities = create_orphan_training_service.create_and_postpone_orphan_training(cmd)

    # THEN

    # 1. Create orphan root group
    create_group_service.create_orphan_group(
        cmd=__convert_to_group_command(training_cmd=create_training_cmd)
    )

    # 2. Create Program tree

    program_tree_identity = create_standard_program_tree_service.create_standard_program_tree(
        CreateStandardVersionCommand(
            offer_acronym=create_training_cmd.abbreviated_title,
            code=create_training_cmd.code,
            year=create_training_cmd.year,
        )
    )

    # 3. Postpone Program tree
    postpone_program_tree_service.postpone_program_tree(
        PostponeProgramTreeCommand(
            from_code=program_tree_identity.code,
            from_year=program_tree_identity.year,
            offer_acronym=create_training_cmd.abbreviated_title,
        )
    )

    # 4. Create standard version of program tree
    program_tree_version_identity = create_standard_version_service.create_standard_program_version(
        CreateStandardVersionCommand(
            offer_acronym=create_training_cmd.abbreviated_title,
            code=create_training_cmd.code,
            year=create_training_cmd.year,
        )
    )

    # 5. Postpone standard version of program tree
    postpone_tree_version_service.postpone_program_tree_version(
        PostponeProgramTreeVersionCommand(
            from_offer_acronym=program_tree_version_identity.offer_acronym,
            from_version_name=program_tree_version_identity.version_name,
            from_year=program_tree_version_identity.year,
            from_is_transition=program_tree_version_identity.is_transition,
            from_code=create_training_cmd.code
        )
    )

    return training_identities


def __convert_to_group_command(training_cmd: command.CreateTrainingCommand) -> command.CreateOrphanGroupCommand:
    return command.CreateOrphanGroupCommand(
        code=training_cmd.code,
        year=training_cmd.year,
        type=training_cmd.type,
        abbreviated_title=training_cmd.abbreviated_title,
        title_fr=training_cmd.title_fr,
        title_en=training_cmd.title_en,
        credits=training_cmd.credits,
        constraint_type=training_cmd.constraint_type,
        min_constraint=training_cmd.min_constraint,
        max_constraint=training_cmd.max_constraint,
        management_entity_acronym=training_cmd.management_entity_acronym,
        teaching_campus_name=training_cmd.teaching_campus_name,
        organization_name=training_cmd.teaching_campus_organization_name,
        remark_fr=training_cmd.remark_fr,
        remark_en=training_cmd.remark_en,
        start_year=training_cmd.year,
        end_year=training_cmd.end_year,
    )

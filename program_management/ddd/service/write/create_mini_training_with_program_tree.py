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
from education_group.ddd.service.write import create_orphan_mini_training_service
from program_management.ddd.command import CreateStandardVersionCommand, PostponeProgramTreeVersionCommand, \
    PostponeProgramTreeCommand
from program_management.ddd.service.write import create_standard_version_service, \
    create_standard_program_tree_service, \
    postpone_program_tree_service_mini_training, \
    postpone_tree_version_service_mini_training


@transaction.atomic()
def create_and_report_mini_training_with_program_tree(
        create_mini_training_cmd: command.CreateMiniTrainingCommand
) -> List['MiniTrainingIdentity']:
    # GIVEN
    cmd = create_mini_training_cmd

    # WHEN
    mini_training_identities = create_orphan_mini_training_service.create_and_postpone_orphan_mini_training(cmd)

    # THEN

    # 1. Create Program tree
    program_tree_identity = create_standard_program_tree_service.create_standard_program_tree(
        CreateStandardVersionCommand(
            offer_acronym=create_mini_training_cmd.abbreviated_title,
            code=create_mini_training_cmd.code,
            start_year=create_mini_training_cmd.year,
        )
    )

    # 2. Create standard version of program tree
    program_tree_version_identity = create_standard_version_service.create_standard_program_version(
        CreateStandardVersionCommand(
            offer_acronym=create_mini_training_cmd.abbreviated_title,
            code=create_mini_training_cmd.code,
            start_year=create_mini_training_cmd.year,
        )
    )

    # 3. Postpone Program tree
    postpone_program_tree_service_mini_training.postpone_program_tree(
        PostponeProgramTreeCommand(
            from_code=program_tree_identity.code,
            from_year=program_tree_identity.year,
            offer_acronym=create_mini_training_cmd.abbreviated_title
        )
    )

    # 4. Postpone standard version of program tree
    postpone_tree_version_service_mini_training.postpone_program_tree_version(
        PostponeProgramTreeVersionCommand(
            from_offer_acronym=program_tree_version_identity.offer_acronym,
            from_version_name=program_tree_version_identity.version_name,
            from_year=program_tree_version_identity.year,
            from_transition_name=program_tree_version_identity.transition_name,
            from_code=create_mini_training_cmd.code
        )
    )

    return mini_training_identities

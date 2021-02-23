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

from django.db import transaction

from education_group.ddd import command as command_education_group
from education_group.ddd.business_types import *
from education_group.ddd.domain import training
from education_group.ddd.service.write import delete_orphan_training_service
from program_management.ddd import command
from program_management.ddd.service.write import delete_standard_program_tree_version_service


@transaction.atomic()
def delete_training_with_program_tree(
        delete_command: command.DeleteTrainingWithProgramTreeCommand
) -> List['TrainingIdentity']:
    delete_program_tree_version_command = command.DeleteProgramTreeVersionCommand(
        offer_acronym=delete_command.offer_acronym,
        version_name=delete_command.version_name,
        transition_name=delete_command.transition_name,
        from_year=delete_command.from_year
    )
    delete_versions_identities = delete_standard_program_tree_version_service.delete_standard_program_tree_version(
        delete_program_tree_version_command
    )

    training_identities = [
        training.TrainingIdentity(acronym=identity.offer_acronym, year=identity.year)
        for identity in delete_versions_identities
    ]
    for training_id in training_identities:
        delete_orphan_training_service.delete_orphan_training(
            command_education_group.DeleteOrphanTrainingCommand(
                acronym=training_id.acronym,
                year=training_id.year
            )
        )
    return training_identities

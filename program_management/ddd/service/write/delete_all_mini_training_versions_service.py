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

from program_management.ddd import command
from program_management.ddd.domain.program_tree_version import STANDARD, ProgramTreeVersionIdentity, NOT_A_TRANSITION
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch
from program_management.ddd.service.write import delete_mini_training_standard_version_service


@transaction.atomic()
def delete_permanently_mini_training_standard_version(
        cmd: command.DeletePermanentlyMiniTrainingStandardVersionCommand
) -> List['ProgramTreeVersionIdentity']:
    program_tree_standard_id = ProgramTreeVersionIdentity(
        offer_acronym=cmd.acronym,
        year=cmd.year,
        version_name=STANDARD,
        transition_name=NOT_A_TRANSITION
    )
    program_tree_version_ids = ProgramTreeVersionIdentitySearch.get_all_program_tree_version_identities(
        program_tree_standard_id
    )

    for program_tree_version_id in program_tree_version_ids:
        delete_mini_training_standard_version_service.delete_mini_training_standard_version(
            command.DeleteMiniTrainingWithStandardVersionCommand(
                mini_training_acronym=program_tree_version_id.offer_acronym,
                year=program_tree_version_id.year,
            )
        )
    return program_tree_version_ids

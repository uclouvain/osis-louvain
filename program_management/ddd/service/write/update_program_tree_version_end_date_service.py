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
from django.db import transaction

from program_management.ddd import command
from program_management.ddd.domain import program_tree_version
from program_management.ddd.repositories import program_tree_version as tree_version_repository
from program_management.ddd.service.write import update_program_tree_version_service


@transaction.atomic()
def update_program_tree_version_end_date(
        update_cmd: 'command.UpdateProgramTreeVersionEndDateCommand'
) -> program_tree_version.ProgramTreeVersionIdentity:
    identity = program_tree_version.ProgramTreeVersionIdentity(
        offer_acronym=update_cmd.from_offer_acronym,
        year=update_cmd.from_year,
        version_name=update_cmd.from_version_name,
        transition_name=update_cmd.from_transition_name,
    )
    tree_version = tree_version_repository.ProgramTreeVersionRepository().get(entity_id=identity)

    return update_program_tree_version_service.update_program_tree_version(
        command=command.UpdateProgramTreeVersionCommand(
            end_year=update_cmd.end_date,
            offer_acronym=update_cmd.from_offer_acronym,
            version_name=update_cmd.from_version_name,
            year=update_cmd.from_year,
            transition_name=update_cmd.from_transition_name,
            title_en=tree_version.title_en,
            title_fr=tree_version.title_fr
        )
    )

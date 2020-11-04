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

from education_group.ddd.service.write import delete_orphan_training_service
from program_management.ddd import command
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity, STANDARD
from program_management.ddd.service.write import delete_specific_version_service, delete_standard_version_service
from education_group.ddd import command as command_education_group


@transaction.atomic()
def delete_training_standard_version(cmd: command.DeleteTrainingStandardVersionCommand) -> ProgramTreeVersionIdentity:
    tree_version_id = delete_standard_version_service.delete_standard_version(
        command.DeleteStandardVersionCommand(
            acronym=cmd.offer_acronym,
            year=cmd.year,
        )
    )
    delete_orphan_training_service.delete_orphan_training(
        command_education_group.DeleteOrphanTrainingCommand(
            acronym=cmd.offer_acronym,
            year=cmd.year,
        )
    )
    return tree_version_id

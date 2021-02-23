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
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity
from program_management.ddd.repositories import program_tree_version as program_tree_version_repository
from program_management.ddd.service.write import delete_program_tree_service
from program_management.ddd.validators.validators_by_business_action import DeleteSpecificVersionValidatorList


@transaction.atomic()
def delete_specific_version(cmd: command.DeleteSpecificVersionCommand) -> ProgramTreeVersionIdentity:
    program_tree_version_id = ProgramTreeVersionIdentity(
        offer_acronym=cmd.acronym,
        year=cmd.year,
        version_name=cmd.version_name,
        transition_name=cmd.transition_name,
    )
    program_tree_version = program_tree_version_repository.ProgramTreeVersionRepository.get(program_tree_version_id)

    DeleteSpecificVersionValidatorList(program_tree_version).validate()

    program_tree_version_repository.ProgramTreeVersionRepository.delete(
        program_tree_version_id,

        # Service Dependancy injection
        delete_program_tree_service=delete_program_tree_service.delete_program_tree
    )
    return program_tree_version_id

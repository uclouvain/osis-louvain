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

from program_management.ddd.business_types import *
from program_management.ddd.command import DeleteProgramTreeVersionCommand
from program_management.ddd.validators._delete_version import EmptyTreeValidator, NoEnrollmentValidator


def delete(command: DeleteProgramTreeVersionCommand) -> None:
    identity = ProgramTreeVersionIdentity(
        command.offer_acronym,
        command.year,
        command.version_name,
        command.is_transition
    )

    program_tree_version = ProgramTreeVersionRepository().get(entity_id=identity)

    error_messages = __validate_delete(program_tree_version, identity)
    if error_messages and len(error_messages) > 0:
        #  TODO : Il me semblait que les service ne pouvait pas retourner de messages????
        return error_messages
    else:
        ProgramTreeVersionRepository().delete(entity_id=identity)


def __validate_delete(
        program_tree_version: 'ProgramTreeVersion',
        identity: 'ProgramTreeVersionIdentity') -> List['BusinessValidationMessage']:
    error_messages = []
    empty_tree_validator = EmptyTreeValidator(tree=program_tree_version)
    no_enrollment_validator = NoEnrollmentValidator(identity=identity)
    if not empty_tree_validator.is_valid():
        error_messages += empty_tree_validator.error_messages
    if not no_enrollment_validator.is_valid():
        error_messages += no_enrollment_validator.error_messages
    return error_messages

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
import itertools
from typing import List

from django.db import transaction

from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception
from program_management.ddd.service.write import delete_standard_version_service


@transaction.atomic()
def delete_standard_program_tree_version(
        #  TODO : create a new command and rename service to ShortenStandardProgramTreeVersionCommand
        delete_command: command.DeleteProgramTreeVersionCommand) -> List['ProgramTreeVersionIdentity']:
    from_year = delete_command.from_year

    deleted_program_tree_versions = []
    for year in itertools.count(from_year):
        try:
            new_delete_command = command.DeleteStandardVersionCommand(
                acronym=delete_command.offer_acronym,
                year=year,
            )
            deleted_program_tree_versions.append(
                delete_standard_version_service.delete_standard_version(new_delete_command)
            )
        except exception.ProgramTreeVersionNotFoundException:
            break

    return deleted_program_tree_versions

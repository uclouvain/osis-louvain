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

from django.db import transaction

from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionBuilder
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.write import create_standard_program_tree_service


@transaction.atomic()
def create_standard_program_version(
        create_standard_cmd: command.CreateStandardVersionCommand
) -> 'ProgramTreeVersionIdentity':

    # GIVEN
    cmd = create_standard_cmd

    # WHEN
    program_tree_version = ProgramTreeVersionBuilder().build_standard_version(
        cmd=cmd,
        tree_repository=ProgramTreeRepository()
    )

    # THEN
    program_tree_version_identity = ProgramTreeVersionRepository().create(program_tree_version)

    return program_tree_version_identity

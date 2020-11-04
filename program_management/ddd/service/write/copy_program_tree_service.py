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

from education_group.ddd.domain import exception
from education_group.ddd.service.write import copy_group_service
from education_group.ddd.service.write.create_group_service import create_orphan_group
from program_management.ddd.command import CopyProgramTreeToNextYearCommand
from program_management.ddd.domain.program_tree import ProgramTreeIdentity, ProgramTreeBuilder
from program_management.ddd.repositories import program_tree as program_tree_repository


@transaction.atomic()
def copy_program_tree_to_next_year(copy_cmd: CopyProgramTreeToNextYearCommand) -> 'ProgramTreeIdentity':
    # GIVEN
    repository = program_tree_repository.ProgramTreeRepository()
    existing_program_tree = repository.get(
        entity_id=ProgramTreeIdentity(
            code=copy_cmd.code,
            year=copy_cmd.year,
        )
    )

    # WHEN
    program_tree_next_year = ProgramTreeBuilder().copy_to_next_year(existing_program_tree, repository)

    # THEN
    # TODO :: remove this try except and add Repository.upsert() function
    try:
        with transaction.atomic():
            identity = repository.create(program_tree_next_year, copy_group_service=copy_group_service.copy_group)
    except exception.CodeAlreadyExistException:
        identity = repository.update(program_tree_next_year)

    return identity

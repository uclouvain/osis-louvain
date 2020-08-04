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

from education_group.ddd.domain.group import GroupIdentity
from education_group.ddd.repository.group import GroupRepository
from education_group.ddd.service.write import create_group_service
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain.program_tree import ProgramTreeBuilder
from program_management.ddd.repositories.node import NodeRepository
from program_management.ddd.repositories.program_tree import ProgramTreeRepository


@transaction.atomic()
def create_standard_program_tree(create_standard_cmd: command.CreateStandardVersionCommand) -> 'ProgramTreeIdentity':

    # GIVEN
    group_identity = GroupIdentity(code=create_standard_cmd.code, year=create_standard_cmd.year)
    root_group = GroupRepository().get(entity_id=group_identity)

    # WHEN
    program_tree = ProgramTreeBuilder().build_from_orphan_group_as_root(
        orphan_group_as_root=root_group,
        node_repository=NodeRepository(),
    )

    # THEN
    program_tree_identity = ProgramTreeRepository().create(
        program_tree=program_tree,
        create_group_service=create_group_service.create_orphan_group
    )

    return program_tree_identity

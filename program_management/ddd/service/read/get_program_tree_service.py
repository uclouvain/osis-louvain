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
from program_management.ddd import command
from program_management.ddd.domain.exception import ProgramTreeNotFoundException
from program_management.ddd.domain.program_tree import ProgramTree, ProgramTreeIdentity
from program_management.ddd.repositories import program_tree as program_tree_repository
from program_management.ddd.service.read import node_identity_service


def get_program_tree(cmd: command.GetProgramTree) -> ProgramTree:
    program_tree_id = ProgramTreeIdentity(code=cmd.code, year=cmd.year)
    return program_tree_repository.ProgramTreeRepository.get(program_tree_id)


# FIXME:: Do not use this service, use get_program_tree above. Idea : do not use id (code & year instead)
def get_program_tree_from_root_element_id(cmd: command.GetProgramTreeFromRootElementIdCommand) -> ProgramTree:
    node_identity = node_identity_service.get_node_identity_from_element_id(
        command.GetNodeIdentityFromElementId(element_id=cmd.root_element_id)
    )
    if not node_identity:
        raise ProgramTreeNotFoundException
    tree_identity = ProgramTreeIdentity(
        code=node_identity.code,
        year=node_identity.year
    )
    return program_tree_repository.ProgramTreeRepository.get(tree_identity)

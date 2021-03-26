#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from program_management.ddd.business_types import *
from program_management.ddd.command import CopyProgramTreePrerequisitesFromProgramTreeCommand
from program_management.ddd.repositories import program_tree as program_tree_repository
from program_management.ddd.domain import program_tree


def copy_program_tree_prerequisites_from_program_tree(
        cmd: 'CopyProgramTreePrerequisitesFromProgramTreeCommand'
) -> 'ProgramTreeIdentity':
    repo = program_tree_repository.ProgramTreeRepository()

    from_tree = repo.get(program_tree.ProgramTreeIdentity(code=cmd.from_code, year=cmd.from_year))
    to_tree = repo.get(program_tree.ProgramTreeIdentity(code=cmd.to_code, year=cmd.to_year))

    program_tree.ProgramTreeBuilder().copy_prerequisites_from_program_tree(from_tree, to_tree)

    repo.update(to_tree)

    return to_tree.entity_id

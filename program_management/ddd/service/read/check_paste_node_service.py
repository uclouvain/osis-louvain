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

import program_management.ddd.command
from program_management.ddd.domain import node
from program_management.ddd.repositories import load_tree, node as node_repository, program_tree
from program_management.ddd.validators import validators_by_business_action


def check_paste(check_command: program_management.ddd.command.CheckPasteNodeCommand) -> None:
    node_to_paste = node_repository.NodeRepository.get(
        node.NodeIdentity(code=check_command.node_to_paste_code, year=check_command.node_to_paste_year)
    )
    tree = load_tree.load(check_command.root_id)

    validators_by_business_action.CheckPasteNodeValidatorList(
        tree,
        node_to_paste,
        check_command,
        program_tree.ProgramTreeRepository()
    ).validate()




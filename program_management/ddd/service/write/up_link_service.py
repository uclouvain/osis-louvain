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
from program_management.ddd.business_types import *
from program_management.ddd.domain.service import identity_search
from program_management.ddd.repositories import program_tree as program_tree_repository


def up_link(command_up: command.OrderUpLinkCommand) -> 'NodeIdentity':
    *_, parent_id, child_id = [int(element_id) for element_id in command_up.path.split("|")]
    repo = program_tree_repository.ProgramTreeRepository()

    tree_identity = identity_search.ProgramTreeIdentitySearch.get_from_element_id(parent_id)
    tree = repo.get(tree_identity)
    parent_node = tree.root_node

    child_identity = identity_search.NodeIdentitySearch.get_from_element_id(child_id)
    child_node = tree.get_node_by_code_and_year(child_identity.code, child_identity.year)

    link_to_up = tree.get_link(parent_node, child_node)
    parent_node = link_to_up.parent
    parent_node.up_child(child_node)

    repo.update(tree)

    return child_node.entity_id

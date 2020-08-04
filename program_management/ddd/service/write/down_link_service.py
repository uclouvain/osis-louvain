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
from program_management.ddd.business_types import *
from program_management.ddd.repositories import persist_tree, load_tree, load_node


@transaction.atomic()
def down_link(command_up: command.OrderDownLinkCommand) -> 'NodeIdentity':
    root_id = int(command_up.path.split("|")[0])
    *_, parent_id, child_id = [int(element_id) for element_id in command_up.path.split("|")]

    parent_node = load_node.load(parent_id)
    child_node = load_node.load(child_id)

    tree = load_tree.load(root_id)
    link_to_down = tree.get_link(parent_node, child_node)
    parent_node = link_to_down.parent
    parent_node.down_child(child_node)

    persist_tree.persist(tree)
    return child_node.entity_id

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
from typing import List

from base.ddd.utils.validation_message import BusinessValidationMessage
from program_management.ddd.repositories import persist_tree, load_tree, load_node
from program_management.models.enums import node_type


#  FIXME Use path in place of parent and child id when group element year form is refactored to use ddd
def up_link(
        root_id: int,
        parent_id: int,
        child_id: int,
        child_type: node_type.NodeType
) -> List[BusinessValidationMessage]:
    parent_node = load_node.load_node_education_group_year(parent_id)
    child_node = load_node.load_by_type(child_type, child_id)

    tree = load_tree.load(root_id)
    link_to_up = tree.get_link(parent_node, child_node)
    parent_node = link_to_up.parent

    previous_order = link_to_up.order - 1
    if not previous_order >= 0:
        return []
    link_to_down = parent_node.children[previous_order]
    link_to_up.order_up()
    link_to_down.order_down()

    persist_tree.persist(tree)
    return []


def down_link(
        root_id: int,
        parent_id: int,
        child_id: int,
        child_type: node_type.NodeType
) -> List[BusinessValidationMessage]:
    parent_node = load_node.load_node_education_group_year(parent_id)
    child_node = load_node.load_by_type(child_type, child_id)

    tree = load_tree.load(root_id)
    link_to_down = tree.get_link(parent_node, child_node)
    parent_node = link_to_down.parent

    next_order = link_to_down.order + 1
    if not len(parent_node.children) > next_order:
        return []
    link_to_up = parent_node.children[next_order]
    link_to_up.order_up()
    link_to_down.order_down()

    persist_tree.persist(tree)
    return []

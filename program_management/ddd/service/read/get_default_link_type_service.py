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
from typing import Optional

from base.models.enums.link_type import LinkTypes
from program_management.ddd import command
from program_management.ddd.domain import node
from program_management.ddd.service.read import node_identity_service
from program_management.ddd.repositories import node as node_repository


def get_default_link_type(get_command: command.GetDefaultLinkType) -> Optional[LinkTypes]:
    parent_id = get_command.path_to_paste.split("|")[-1]
    get_node_identity_command = command.GetNodeIdentityFromElementId(element_id=parent_id)
    parent_node_identity = node_identity_service.get_node_identity_from_element_id(get_node_identity_command)
    if not parent_node_identity:
        return None
    child_node_identity = node.NodeIdentity(code=get_command.child_code, year=get_command.child_year)

    parent_node = node_repository.NodeRepository.get(parent_node_identity)
    child_node = node_repository.NodeRepository.get(child_node_identity)

    if parent_node.is_minor_major_list_choice() and child_node.is_minor_or_deepening():
        return LinkTypes.REFERENCE
    return None

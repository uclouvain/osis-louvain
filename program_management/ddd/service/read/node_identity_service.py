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

from program_management.ddd import command
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch


# TODO: Fix me: This is not an application service because element_id is a technical notion
#  (Path is badly construct... Normally, we should have something like "?path=LDROI1200_2015|...."
def get_node_identity_from_element_id(cmd: command.GetNodeIdentityFromElementId) -> Optional[NodeIdentity]:
    return NodeIdentitySearch.get_from_element_id(cmd.element_id)

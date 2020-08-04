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

from django.db import transaction

from program_management.ddd.business_types import *

from program_management.ddd.command import BulkUpdateLinkCommand
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.repositories.program_tree import ProgramTreeRepository


@transaction.atomic()
def bulk_update_links(cmd: BulkUpdateLinkCommand) -> List['Link']:
    tree_id = ProgramTreeIdentity(code=cmd.parent_node_code, year=cmd.parent_node_year)
    tree = ProgramTreeRepository.get(tree_id)

    links_updated = []
    for update_cmd in cmd.update_link_cmds:
        child_id = NodeIdentity(code=update_cmd.child_node_code, year=update_cmd.child_node_year)
        link_updated = tree.update_link(
            parent_path=str(tree.root_node.node_id),
            child_id=child_id,

            relative_credits=update_cmd.relative_credits,
            access_condition=update_cmd.access_condition,
            is_mandatory=update_cmd.is_mandatory,
            block=update_cmd.block,
            link_type=update_cmd.link_type,
            comment=update_cmd.comment,
            comment_english=update_cmd.comment_english
        )
        links_updated.append(link_updated)
    ProgramTreeRepository.update(tree)
    return links_updated

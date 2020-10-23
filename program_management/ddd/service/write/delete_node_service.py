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

from base.models.enums.education_group_types import GroupType, TrainingType, MiniTrainingType
from education_group.ddd import command as command_education_group
from education_group.ddd.domain import exception
from education_group.ddd.service.write import delete_orphan_group_service, delete_orphan_training_service, \
    delete_orphan_mini_training_service
from program_management.ddd import command
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain import exception as program_management_exception


@transaction.atomic()
def delete_node(cmd: command.DeleteNodeCommand) -> None:
    node_id = NodeIdentity(code=cmd.code, year=cmd.year)

    try:
        cmd = command_education_group.DeleteOrphanGroupCommand(code=node_id.code, year=node_id.year)
        try:
            delete_orphan_group_service.delete_orphan_group(cmd)
        except exception.GroupNotFoundException:
            pass
    except (exception.GroupIsBeingUsedException):
        raise program_management_exception.NodeIsUsedException

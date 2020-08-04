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
from education_group.ddd.domain.service.identity_search import TrainingIdentitySearch
from education_group.ddd.service.write import delete_orphan_group_service, delete_orphan_training_service, \
    delete_orphan_mini_training_service
from program_management.ddd import command
from education_group.ddd import command as command_education_group
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch


@transaction.atomic()
def delete_node(cmd: command.DeleteNodeCommand) -> None:
    node_id = NodeIdentity(code=cmd.code, year=cmd.year)

    if cmd.node_type in GroupType.get_names():
        cmd = command_education_group.DeleteOrphanGroupCommand(code=node_id.code, year=node_id.year)
        delete_orphan_group_service.delete_orphan_group(cmd)
    elif cmd.node_type in TrainingType.get_names():
        training_id = TrainingIdentitySearch().get_from_node_identity(node_id)
        cmd = command_education_group.DeleteOrphanTrainingCommand(
            acronym=training_id.acronym,
            year=training_id.year
        )
        delete_orphan_training_service.delete_orphan_training(cmd)
    elif cmd.node_type in MiniTrainingType.get_names():
        # TODO: change With MiniTrainingIdentitySearch()
        tree_version_id = ProgramTreeVersionIdentitySearch().get_from_node_identity(node_id)
        cmd = command_education_group.DeleteOrphanMiniTrainingCommand(
            acronym=tree_version_id.offer_acronym,
            year=tree_version_id.year
        )
        delete_orphan_mini_training_service.delete_orphan_mini_training(cmd)

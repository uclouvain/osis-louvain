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

from education_group.ddd import command
from education_group.ddd.domain import mini_training
from education_group.ddd.repository import mini_training as mini_training_repository
from education_group.ddd.service.write import postpone_mini_training_and_orphan_group_modifications_service, \
    create_group_service


@transaction.atomic()
def create_and_postpone_orphan_mini_training(
        cmd: command.CreateMiniTrainingCommand) -> List['mini_training.MiniTrainingIdentity']:
    mini_training_object = mini_training.MiniTrainingBuilder().build_from_create_cmd(cmd)

    mini_training_identity = mini_training_repository.MiniTrainingRepository.create(mini_training_object)
    group_identity = create_group_service.create_orphan_group(__convert_to_create_group_command(cmd))

    mini_training_identities = postpone_mini_training_and_orphan_group_modifications_service.\
        postpone_mini_training_and_orphan_group_modifications(
            command.PostponeMiniTrainingAndGroupModificationCommand(
                postpone_from_abbreviated_title=cmd.abbreviated_title,
                postpone_from_year=cmd.year,

                code=cmd.code,
                status=cmd.status,
                credits=cmd.credits,
                title_fr=cmd.title_fr,
                title_en=cmd.title_en,
                keywords=cmd.keywords,
                management_entity_acronym=cmd.management_entity_acronym,
                end_year=cmd.end_year,
                teaching_campus_name=cmd.teaching_campus_name,
                organization_name=cmd.organization_name,
                constraint_type=cmd.constraint_type,
                min_constraint=cmd.min_constraint,
                max_constraint=cmd.max_constraint,
                remark_fr=cmd.remark_fr,
                remark_en=cmd.remark_en,
                schedule_type=cmd.schedule_type,
            )
        )

    return mini_training_identities


def __convert_to_create_group_command(cmd: command.CreateMiniTrainingCommand) -> command.CreateOrphanGroupCommand:
    return command.CreateOrphanGroupCommand(
        code=cmd.code,
        year=cmd.year,
        type=cmd.type,
        abbreviated_title=cmd.abbreviated_title,
        title_fr=cmd.title_fr,
        title_en=cmd.title_en,
        credits=cmd.credits,
        constraint_type=cmd.constraint_type,
        min_constraint=cmd.min_constraint,
        max_constraint=cmd.max_constraint,
        management_entity_acronym=cmd.management_entity_acronym,
        teaching_campus_name=cmd.teaching_campus_name,
        organization_name=cmd.organization_name,
        remark_fr=cmd.remark_fr,
        remark_en=cmd.remark_en,
        start_year=cmd.start_year,
        end_year=cmd.end_year,
    )

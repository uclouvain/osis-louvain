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

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.command import UpdateGroupCommand
from education_group.ddd.domain import mini_training
from education_group.ddd.domain._entity import Entity
from education_group.ddd.domain._titles import Titles
from education_group.ddd.repository import mini_training as mini_training_repository
from education_group.ddd.service.write import update_group_service


@transaction.atomic()
def update_mini_training_and_group(cmd: command.UpdateMiniTrainingAndGroupCommand) -> 'MiniTrainingIdentity':
    errors = set()
    try:
        mini_training_identity = mini_training.MiniTrainingIdentity(acronym=cmd.abbreviated_title, year=cmd.year)
        mini_training_domain_obj = mini_training_repository.MiniTrainingRepository.get(mini_training_identity)

        mini_training_domain_obj.update(__convert_command_to_update_mini_training_data(cmd))
        mini_training_repository.MiniTrainingRepository.update(mini_training_domain_obj)
    except MultipleBusinessExceptions as e:
        errors |= e.exceptions

    try:
        update_group_service.update_group(__convert_to_update_group_command(cmd))
    except MultipleBusinessExceptions as e:
        errors = e.exceptions

    if errors:
        raise MultipleBusinessExceptions(exceptions=errors)

    return mini_training_identity


def __convert_command_to_update_mini_training_data(
        cmd: command.UpdateMiniTrainingAndGroupCommand) -> 'mini_training.UpdateMiniTrainingData':
    return mini_training.UpdateMiniTrainingData(
        credits=cmd.credits,
        titles=Titles(
            title_fr=cmd.title_fr,
            title_en=cmd.title_en,
        ),
        status=ActiveStatusEnum[cmd.status],
        keywords=cmd.keywords,
        management_entity=Entity(acronym=cmd.management_entity_acronym),
        end_year=cmd.end_year,
        schedule_type=ScheduleTypeEnum[cmd.schedule_type],
    )


def __convert_to_update_group_command(cmd: command.UpdateMiniTrainingAndGroupCommand) -> 'UpdateGroupCommand':
    return UpdateGroupCommand(
            code=cmd.code,
            year=cmd.year,
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
            end_year=cmd.end_year,
    )

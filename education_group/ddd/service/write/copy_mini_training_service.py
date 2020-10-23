##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.db import transaction

from education_group.ddd import command
from education_group.ddd.domain import exception
from education_group.ddd.domain.mini_training import MiniTrainingIdentity, MiniTrainingBuilder
from education_group.ddd.repository import mini_training as mini_training_repository
from education_group.ddd.service.write import copy_group_service


@transaction.atomic()
def copy_mini_training_to_next_year(copy_cmd: command.CopyMiniTrainingToNextYearCommand) -> 'MiniTrainingIdentity':
    # GIVEN
    repository = mini_training_repository.MiniTrainingRepository()
    existing_mini_training = repository.get(
        entity_id=MiniTrainingIdentity(acronym=copy_cmd.acronym, year=copy_cmd.postpone_from_year)
    )

    # WHEN
    mini_training_next_year = MiniTrainingBuilder().copy_to_next_year(existing_mini_training, repository)
    try:
        with transaction.atomic():
            identity = repository.create(mini_training_next_year)
    except exception.CodeAlreadyExistException:
        identity = repository.update(mini_training_next_year)

    cmd_copy_group = command.CopyGroupCommand(
        from_code=existing_mini_training.code,
        from_year=copy_cmd.postpone_from_year
    )
    copy_group_service.copy_group(cmd_copy_group)

    return identity

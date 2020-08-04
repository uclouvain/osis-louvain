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
from education_group.ddd.domain.mini_training import MiniTrainingBuilder
from education_group.ddd.repository.mini_training import MiniTrainingRepository
from education_group.ddd.service.write import postpone_mini_training_service


@transaction.atomic()
def create_and_postpone_orphan_mini_training(
        cmd: command.CreateMiniTrainingCommand) -> List['mini_training.MiniTrainingIdentity']:
    mini_training_object = MiniTrainingBuilder().build_from_create_cmd(cmd)

    mini_training_identity = MiniTrainingRepository.create(mini_training_object)
    mini_training_identities = postpone_mini_training_service.postpone_mini_training(
        command.PostponeMiniTrainingCommand(
            acronym=cmd.abbreviated_title,
            postpone_from_year=cmd.year
        )
    )

    return [mini_training_identity] + mini_training_identities

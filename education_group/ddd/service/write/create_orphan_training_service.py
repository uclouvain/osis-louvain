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
from typing import List

from django.db import transaction

from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain.training import TrainingBuilder
from education_group.ddd.repository.training import TrainingRepository
from education_group.ddd.service.write import postpone_training_service


@transaction.atomic()
def create_and_postpone_orphan_training(create_training_cmd: command.CreateTrainingCommand) -> List['TrainingIdentity']:
    # GIVEN
    cmd = create_training_cmd

    # WHEN
    training = TrainingBuilder().create_training(cmd)

    # THEN
    training_id = TrainingRepository.create(training)
    training_identities = postpone_training_service.postpone_training(
        command.PostponeTrainingCommand(
            acronym=training_id.acronym,
            postpone_from_year=training_id.year,
        )
    )

    return [training_id] + training_identities

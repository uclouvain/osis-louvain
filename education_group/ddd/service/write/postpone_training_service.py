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
from education_group.ddd.domain.service.calculate_end_postponement import CalculateEndPostponement
from education_group.ddd.domain.training import TrainingIdentity
from education_group.ddd.repository.training import TrainingRepository
from education_group.ddd.service.write import copy_training_service


@transaction.atomic()
def postpone_training(postpone_cmd: command.PostponeTrainingCommand) -> List['TrainingIdentity']:
    identities_created = []

    # GIVEN
    from_year = postpone_cmd.postpone_from_year
    copy_from_training = TrainingRepository().get(
        entity_id=TrainingIdentity(acronym=postpone_cmd.acronym, year=from_year)
    )
    end_postponement_year = CalculateEndPostponement.calculate_year_of_end_postponement(copy_from_training)

    # WHEN
    while from_year < end_postponement_year:

        identity_next_year = copy_training_service.copy_training_to_next_year(
            copy_cmd=command.CopyTrainingToNextYearCommand(
                acronym=postpone_cmd.acronym,
                postpone_from_year=from_year
            )
        )

        # THEN
        identities_created.append(identity_next_year)
        from_year += 1

    return identities_created

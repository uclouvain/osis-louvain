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
from education_group.ddd.domain.exception import TrainingNotFoundException
from education_group.ddd.domain.training import TrainingBuilder, TrainingIdentity
from education_group.ddd.repository import training as training_repository


@transaction.atomic()
def copy_certificate_aims_to_next_year(copy_cmd: command.CopyCertificateAimsToNextYearCommand) -> 'TrainingIdentity':
    # GIVEN
    repository = training_repository.TrainingRepository()
    existing_training = repository.get(
        entity_id=TrainingIdentity(acronym=copy_cmd.acronym, year=copy_cmd.postpone_from_year)
    )

    try:
        # WHEN
        training_next_year = TrainingBuilder().copy_aims_to_next_year(existing_training, repository)

        # THEN
        identity = repository.update(training_next_year)
        return identity

    except TrainingNotFoundException:
        # do nothing when next year has no training
        pass

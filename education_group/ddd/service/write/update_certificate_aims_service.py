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

from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain import training
from education_group.ddd.domain._diploma import Diploma, DiplomaAim, DiplomaAimIdentity
from education_group.ddd.repository import training as training_repository


@transaction.atomic()
def update_certificate_aims(cmd: command.UpdateCertificateAimsCommand) -> 'TrainingIdentity':
    training_identity = training.TrainingIdentity(acronym=cmd.acronym, year=cmd.year)
    training_domain_obj = training_repository.TrainingRepository.get(training_identity)
    training_domain_obj.update_aims(__convert_command_to_update_diploma_data(cmd))
    training_repository.TrainingRepository.update(training_domain_obj)
    return training_identity


def __convert_command_to_update_diploma_data(
        cmd: command.UpdateCertificateAimsCommand
) -> 'training.UpdateDiplomaData':
    return training.UpdateDiplomaData(
        diploma=Diploma(
            aims=[DiplomaAim(entity_id=DiplomaAimIdentity(section, code), description="")
                  for code, section in (cmd.aims or [])]
        ),
    )

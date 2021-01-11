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

from education_group.ddd.command import GetTrainingEmptyFieldsOnWarningCommand
from education_group.ddd.domain import exception
from education_group.ddd.domain.service import fields_with_alert_when_empty
from education_group.ddd.domain.training import TrainingIdentity
from education_group.ddd.repository import training as training_repository


def check_training_empty_fields_on_warning(cmd: 'GetTrainingEmptyFieldsOnWarningCommand') -> None:
    training_identity = TrainingIdentity(acronym=cmd.acronym, year=cmd.year)
    training = training_repository.TrainingRepository().get(training_identity)

    fields_to_check = fields_with_alert_when_empty.get_for_training(training.type)
    fields_on_warning = []
    if "main_domain" in fields_to_check and training.main_domain is None:
        fields_on_warning.append("main_domain")
    if "funding_orientation" in fields_to_check and \
            (training.funding is None or training.funding.funding_orientation is None):
        fields_on_warning.append("funding_orientation")
    if "international_funding_orientation" in fields_to_check and \
            (training.funding is None or training.funding.international_funding_orientation is None):
        fields_on_warning.append("international_funding_orientation")

    if fields_on_warning:
        raise exception.TrainingEmptyFieldException(empty_fields=fields_on_warning)

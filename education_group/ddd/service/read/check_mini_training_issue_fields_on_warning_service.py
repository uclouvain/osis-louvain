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
from education_group.ddd.command import GetMiniTrainingIssueFieldsOnWarningCommand
from education_group.ddd.domain import exception
from education_group.ddd.domain.mini_training import MiniTrainingIdentity
from education_group.ddd.domain.service import fields_with_alert_when_issue
from education_group.ddd.domain.service.get_entity_active import ActiveEntity
from education_group.ddd.repository import mini_training as mini_training_repository


def check_mini_training_issue_fields_on_warning(cmd: 'GetMiniTrainingIssueFieldsOnWarningCommand') -> None:
    mini_training_identity = MiniTrainingIdentity(acronym=cmd.acronym, year=cmd.year)
    mini_training = mini_training_repository.MiniTrainingRepository().get(mini_training_identity)

    fields_to_check = fields_with_alert_when_issue.get_for_mini_training(mini_training.type)
    management_entity_active = ActiveEntity.is_entity_active_for_year(
        mini_training.management_entity.acronym,
        mini_training_identity.year
    )
    fields_on_warning = []
    if "management_entity" in fields_to_check and not management_entity_active:
        fields_on_warning.append("management_entity")

    if fields_on_warning:
        raise exception.MiniTrainingAlertFieldException(empty_fields=fields_on_warning)

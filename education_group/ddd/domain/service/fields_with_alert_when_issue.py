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
from typing import Iterable

from django.db.models.functions import Substr

from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from base.models.validation_rule import ValidationRule


def get_for_training(training_type: TrainingType) -> Iterable[str]:
    field_references = ".".join(["TrainingForm", training_type.name])
    fields = ValidationRule.objects.filter(
        field_reference__startswith=field_references,
        status_field='ALERT'
    ).annotate(
        field_name=Substr("field_reference", len(field_references) + 2)
    ).values_list("field_name", flat=True)
    fields = list(fields)
    return fields


def get_for_mini_training(training_type: MiniTrainingType) -> Iterable[str]:
    field_references = ".".join(["MiniTrainingForm", training_type.name])
    fields = ValidationRule.objects.filter(
        field_reference__startswith=field_references,
        status_field='ALERT'
    ).annotate(
        field_name=Substr("field_reference", len(field_references) + 2)
    ).values_list("field_name", flat=True)
    fields = list(fields)
    return fields


def get_for_group(training_type: GroupType) -> Iterable[str]:
    field_references = ".".join(["GroupForm", training_type.name])
    fields = ValidationRule.objects.filter(
        field_reference__startswith=field_references,
        status_field='ALERT'
    ).annotate(
        field_name=Substr("field_reference", len(field_references) + 2)
    ).values_list("field_name", flat=True)
    fields = list(fields)
    return fields

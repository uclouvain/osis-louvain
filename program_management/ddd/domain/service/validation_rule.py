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

from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType, MiniTrainingType
from base.models.validation_rule import ValidationRule
from osis_common.ddd import interface


class FieldValidationRule(interface.DomainService):

    @classmethod
    def get(cls, node_type: EducationGroupTypesEnum, field_name: str) -> ValidationRule:
        prefix = 'GroupForm'
        if isinstance(node_type, TrainingType):
            prefix = 'TrainingForm'
        elif isinstance(node_type, MiniTrainingType):
            prefix = 'MiniTrainingForm'
        field_reference_value = '{prefix}.{type}.{field_name}'.format(
            prefix=prefix,
            type=node_type.name,
            field_name=field_name,
        )
        return ValidationRule.objects.get(field_reference=field_reference_value)

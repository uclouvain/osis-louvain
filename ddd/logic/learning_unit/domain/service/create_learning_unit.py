##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial
from typing import List

from base.ddd.utils.business_validator import execute_functions_and_aggregate_exceptions
from ddd.logic.learning_unit.builder.learning_unit_builder import LearningUnitBuilder
from ddd.logic.learning_unit.commands import CreateLearningUnitCommand
from ddd.logic.learning_unit.domain.model.learning_unit import LearningUnitIdentity
from ddd.logic.learning_unit.domain.model.responsible_entity import UclEntity
from ddd.logic.learning_unit.domain.validator.exceptions import InvalidResponsibleEntityTypeOrCodeException
from osis_common.ddd import interface


class CreateLearningUnit(interface.DomainService):

    @classmethod
    def create(
            cls,
            ucl_entity: 'UclEntity',
            cmd: 'CreateLearningUnitCommand',
            all_existing_identities: List['LearningUnitIdentity']
    ):
        __, learning_unit = execute_functions_and_aggregate_exceptions(
            partial(_should_be_responsible_entity, ucl_entity),
            partial(LearningUnitBuilder.build_from_command, cmd, all_existing_identities, ucl_entity.entity_id),
        )
        return learning_unit


def _should_be_responsible_entity(ucl_entity: 'UclEntity'):
    if not ucl_entity.is_responsible_entity():
        raise InvalidResponsibleEntityTypeOrCodeException(ucl_entity.code)

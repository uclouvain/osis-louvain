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
from django.db import transaction

from ddd.logic.learning_unit.builder.ucl_entity_identity_builder import UclEntityIdentityBuilder
from ddd.logic.learning_unit.commands import CreateLearningUnitCommand
from ddd.logic.learning_unit.domain.model.learning_unit import LearningUnitIdentity
from ddd.logic.learning_unit.domain.service.create_learning_unit import CreateLearningUnit
from ddd.logic.learning_unit.repository.i_learning_unit import ILearningUnitRepository
from ddd.logic.learning_unit.repository.i_ucl_entity import IUclEntityRepository


@transaction.atomic()
def create_learning_unit(
        cmd: CreateLearningUnitCommand,
        learning_unit_repository: ILearningUnitRepository,
        entity_repository: IUclEntityRepository,
) -> LearningUnitIdentity:
    # GIVEN
    all_existing_identities = learning_unit_repository.get_identities()
    entity = entity_repository.get(
        entity_id=UclEntityIdentityBuilder.build_from_code(cmd.responsible_entity_code),
    )

    # WHEN
    learning_unit = CreateLearningUnit.create(entity, cmd, all_existing_identities)

    # THEN
    learning_unit_repository.save(learning_unit)

    return learning_unit.entity_id

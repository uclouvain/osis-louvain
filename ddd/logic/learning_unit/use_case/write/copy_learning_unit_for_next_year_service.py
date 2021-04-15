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

from ddd.logic.learning_unit.builder.learning_unit_builder import LearningUnitBuilder
from ddd.logic.learning_unit.builder.learning_unit_identity_builder import LearningUnitIdentityBuilder
from ddd.logic.learning_unit.commands import CopyLearningUnitToNextYearCommand
from ddd.logic.learning_unit.domain.model.learning_unit import LearningUnitIdentity
from infrastructure.learning_unit.repository.learning_unit import LearningUnitRepository


@transaction.atomic()
def copy_learning_unit_to_next_year(cmd: CopyLearningUnitToNextYearCommand) -> 'LearningUnitIdentity':
    # GIVEN
    repository = LearningUnitRepository()
    learning_unit = repository.get(entity_id=LearningUnitIdentityBuilder.build_from_command(cmd))
    all_existing_learning_unit_identities = repository.get_identities()

    # WHEN
    learning_unit_net_year = LearningUnitBuilder.copy_to_next_year(learning_unit, all_existing_learning_unit_identities)

    # THEN
    repository.save(learning_unit_net_year)

    return learning_unit.entity_id

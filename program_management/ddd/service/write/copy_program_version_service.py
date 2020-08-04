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

from program_management.ddd.command import CopyTreeVersionToNextYearCommand
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionBuilder, ProgramTreeVersionIdentity
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository


@transaction.atomic()
def copy_tree_version_to_next_year(copy_cmd: CopyTreeVersionToNextYearCommand) -> 'ProgramTreeVersionIdentity':
    # GIVEN
    repository = ProgramTreeVersionRepository()
    existing_program_tree_version = repository.get(
        entity_id=ProgramTreeVersionIdentity(
            offer_acronym=copy_cmd.from_offer_acronym,
            year=copy_cmd.from_year,
            version_name=copy_cmd.from_version_name,
            is_transition=copy_cmd.from_is_transition,
        )
    )

    # WHEN
    tree_version_next_year = ProgramTreeVersionBuilder().copy_to_next_year(existing_program_tree_version, repository)

    # THEN
    identity = repository.create(tree_version_next_year)

    return identity

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
from typing import List

from program_management.ddd.command import PostponeProgramTreeVersionCommand, CreateProgramTreeSpecificVersionCommand, \
    PostponeProgramTreeCommand
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.write import postpone_tree_specific_version_service, \
    postpone_program_tree_service, create_program_tree_specific_version_service


def create_and_postpone_program_tree_specific_version(
        command: 'CreateProgramTreeSpecificVersionCommand'
) -> List[ProgramTreeVersionIdentity]:

    identity = create_program_tree_specific_version_service.create_program_tree_specific_version(command)
    tree_version = ProgramTreeVersionRepository().get(identity)

    postpone_program_tree_service.postpone_program_tree(
        PostponeProgramTreeCommand(
            from_code=tree_version.program_tree_identity.code,
            from_year=tree_version.program_tree_identity.year,
            offer_acronym=identity.offer_acronym,
        )
    )

    created_identities = postpone_tree_specific_version_service.postpone_program_tree_version(
        PostponeProgramTreeVersionCommand(
            from_offer_acronym=identity.offer_acronym,
            from_year=identity.year,
            from_transition_name=identity.transition_name,
            from_version_name=identity.version_name,
        )
    )

    return [identity] + created_identities

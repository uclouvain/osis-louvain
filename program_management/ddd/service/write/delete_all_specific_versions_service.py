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
from typing import List

from django.db import transaction

from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.repositories import program_tree_version as program_tree_version_repository
from program_management.ddd.service.write import delete_specific_version_service


@transaction.atomic()
def delete_permanently_tree_version(
        cmd: command.DeletePermanentlyTreeVersionCommand
) -> List['ProgramTreeVersionIdentity']:

    tree_versions_to_delete = program_tree_version_repository.ProgramTreeVersionRepository().search(
        version_name=cmd.version_name,
        offer_acronym=cmd.acronym,
        transition_name=cmd.transition_name,
    )
    tree_versions_identities = []
    for tree_version in tree_versions_to_delete:
        deleted_tree_version_identity = _call_delete_specific_version_service(tree_version)
        tree_versions_identities.append(deleted_tree_version_identity)

    return tree_versions_identities


def _call_delete_specific_version_service(tree_version: 'ProgramTreeVersion') -> 'ProgramTreeVersionIdentity':
    return delete_specific_version_service.delete_specific_version(
        command.DeleteSpecificVersionCommand(
            acronym=tree_version.entity_identity.offer_acronym,
            year=tree_version.entity_identity.year,
            version_name=tree_version.entity_identity.version_name,
            transition_name=tree_version.entity_identity.transition_name,
        )
    )

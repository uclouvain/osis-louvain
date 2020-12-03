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

from django.db import transaction

from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain import group, exception
from education_group.ddd.domain._titles import Titles
from education_group.ddd.repository import group as group_repository
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository


@transaction.atomic()
def copy_group(cmd: command.CopyGroupCommand) -> 'GroupIdentity':
    repository = group_repository.GroupRepository()
    existing_group = repository.get(
        entity_id=group.GroupIdentity(code=cmd.from_code, year=cmd.from_year)
    )

    group_next_year = group.GroupBuilder().copy_to_next_year(existing_group, repository)

    try:
        with transaction.atomic():
            group_id = repository.create(group_next_year)
    except exception.CodeAlreadyExistException:
        group_id = repository.update(group_next_year)

    _update_others_version_groups(existing_group)

    return group_id


def _update_others_version_groups(from_group: 'Group'):
    node_id = NodeIdentity(code=from_group.code, year=from_group.year + 1)
    versions = ProgramTreeVersionRepository().search_all_versions_from_root_node(node_id)
    for version in versions:
        if not version.is_standard:
            tree_identity = version.program_tree_identity
            version_group_identity = group.GroupIdentity(code=tree_identity.code, year=tree_identity.year)
            existing_group_version = group_repository.GroupRepository().get(version_group_identity)
            existing_group_version.update_unversioned_fields(
                abbreviated_title=from_group.abbreviated_title,
                titles=Titles(title_fr=from_group.titles.title_fr, title_en=from_group.titles.title_en),
            )
            group_repository.GroupRepository().update(existing_group_version)

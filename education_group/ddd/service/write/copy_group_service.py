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
from education_group.ddd.repository import group as group_repository


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
    return group_id

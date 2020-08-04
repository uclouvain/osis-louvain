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

from education_group.ddd import command
from education_group.ddd.domain import group
from education_group.ddd.business_types import *
from education_group.ddd.service.read import get_group_service as group_service_read
from education_group.ddd.service.write.create_group_service import create_orphan_group


@transaction.atomic()
def copy_group(cmd: command.CopyGroupCommand) -> List['GroupIdentity']:
    """
    Copy an existing group from the year of this group (=excluded) to a specific year (=included)
    """
    group_ids = []

    from_year = cmd.from_year
    while from_year < cmd.to_year:
        cmd_get_group = command.GetGroupCommand(code=cmd.from_code, year=from_year)
        grp = group_service_read.get_group(cmd_get_group)

        group_next_year = group.builder.build_next_year_group(from_group=grp)

        group_next_year_id = create_orphan_group(__convert_group_to_command(group_next_year))

        group_ids.append(group_next_year_id)
        from_year += 1

    return group_ids


def __convert_group_to_command(group_next_year: 'Group') -> command.CreateOrphanGroupCommand:
    return command.CreateOrphanGroupCommand(
        code=group_next_year.code,
        year=group_next_year.year,
        type=group_next_year.type.name,
        abbreviated_title=group_next_year.abbreviated_title,
        title_fr=group_next_year.titles.title_fr,
        title_en=group_next_year.titles.title_en,
        credits=group_next_year.credits,
        constraint_type=group_next_year.content_constraint.type.name
        if group_next_year.content_constraint.type else None,
        min_constraint=group_next_year.content_constraint.minimum,
        max_constraint=group_next_year.content_constraint.maximum,
        management_entity_acronym=group_next_year.management_entity.acronym,
        teaching_campus_name=group_next_year.teaching_campus.name,
        organization_name=group_next_year.teaching_campus.university_name,
        remark_fr=group_next_year.remark.text_fr,
        remark_en=group_next_year.remark.text_en,
        start_year=group_next_year.start_year,
        end_year=group_next_year.end_year
    )

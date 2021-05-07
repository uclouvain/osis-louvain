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

from education_group.calendar.education_group_switch_calendar import EducationGroupSwitchCalendar
from education_group.ddd import command
from education_group.ddd.domain.group import GroupIdentity
from education_group.ddd.domain.service.conflicted_fields import ConflictedFields
from education_group.ddd.domain.service.postpone_group import PostponeOrphanGroup
from education_group.ddd.repository import group as group_repository
from education_group.ddd.service.write import copy_group_service
from program_management.ddd.domain.service.calculate_end_postponement import CalculateEndPostponement
from program_management.ddd.repositories import load_authorized_relationship


# DO NOT SET @transaction.atomic() because it breaks the update in case of GroupCopyConsistencyException
def update_group(cmd: command.UpdateGroupCommand) -> List['GroupIdentity']:

    # GIVEN
    group_identity = GroupIdentity(code=cmd.code, year=cmd.year)
    grp = group_repository.GroupRepository.get(group_identity)
    authorized_relationships = load_authorized_relationship.load()
    conflicted_fields = ConflictedFields.get_group_conflicted_fields(grp.entity_id)

    # WHEN
    grp.update(cmd)

    # THEN
    group_repository.GroupRepository.update(grp)
    updated_identities = [grp.entity_id]

    updated_identities += PostponeOrphanGroup.postpone(
        updated_group=grp,
        conflicted_fields=conflicted_fields,
        end_postponement_calculator=CalculateEndPostponement(),
        copy_group_service=copy_group_service.copy_group,
        authorized_relationships=authorized_relationships,
        calendar=EducationGroupSwitchCalendar(),
    )

    return updated_identities

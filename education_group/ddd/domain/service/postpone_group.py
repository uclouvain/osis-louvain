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
from typing import Dict, List

from base.models.authorized_relationship import AuthorizedRelationshipList
from education_group.calendar.education_group_switch_calendar import EducationGroupSwitchCalendar
from education_group.ddd import command
from education_group.ddd.domain.exception import GroupCopyConsistencyException
from education_group.ddd.domain.group import Group
from education_group.ddd.domain.service.conflicted_fields import Year, FieldLabel
from osis_common.ddd import interface
from osis_common.ddd.interface import ApplicationService
from program_management.ddd.domain.service.calculate_end_postponement import CalculateEndPostponement


class PostponeOrphanGroup(interface.DomainService):
    @classmethod
    def postpone(
            cls,
            updated_group: 'Group',
            conflicted_fields: Dict[Year, List[FieldLabel]],
            end_postponement_calculator: 'CalculateEndPostponement',
            copy_group_service: ApplicationService,
            authorized_relationships: 'AuthorizedRelationshipList',
            calendar: 'EducationGroupSwitchCalendar'
    ):
        identities = []
        closest_working_year = min(calendar.get_target_years_opened())
        is_in_past = updated_group.year < closest_working_year
        if not is_in_past and authorized_relationships.is_mandatory_child_type(updated_group.type):
            # means that this group has been automatically created by the system
            # behind 'trainings' and 'minitrainings' Nodes/groups in ProgramTree

            end_postponement_year = end_postponement_calculator.calculate_end_postponement_year_for_orphan_group(
                group=updated_group
            )
            for year in range(updated_group.year, end_postponement_year):
                if year + 1 in conflicted_fields:
                    break  # Do not copy info from year to N+1 because conflict detected
                identity_next_year = copy_group_service(
                    command.CopyGroupCommand(
                        from_code=updated_group.code,
                        from_year=year
                    )
                )
                identities.append(identity_next_year)
            if conflicted_fields:
                first_conflict_year = min(conflicted_fields.keys())
                raise GroupCopyConsistencyException(first_conflict_year, conflicted_fields[first_conflict_year])
        return identities

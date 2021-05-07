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
from typing import List, Tuple

from education_group.calendar.education_group_switch_calendar import EducationGroupSwitchCalendar
from education_group.ddd.domain.service.conflicted_fields import ConflictedFields
from osis_common.ddd import interface
from program_management.ddd.business_types import *
from program_management.ddd.command import UpdateLinkCommand
from program_management.ddd.domain import report_events
from program_management.ddd.domain.service.search_program_trees_in_future import SearchProgramTreesInFuture


class PostponeLink(interface.DomainService):

    @classmethod
    def postpone(
            cls,
            working_tree: 'ProgramTree',
            link_before_update: 'Link',
            link_after_update: 'Link',
            trees_through_years: List['ProgramTree'],
            trees_in_future_searcher: 'SearchProgramTreesInFuture',
            conflicted_fields_checker: 'ConflictedFields',
            calendar: 'EducationGroupSwitchCalendar'
    ) -> Tuple[List['Link'], List['ProgramTree']]:
        updated_links = []
        updated_program_trees = []
        closest_working_year = min(calendar.get_target_years_opened())
        is_in_past = working_tree.year < closest_working_year
        if not is_in_past:
            is_mandatory_child_type = working_tree.authorized_relationships.is_mandatory_child_type(
                link_before_update.child.node_type
            )
            if is_mandatory_child_type:
                # means that the child group of this link has been automatically created by the system in ProgramTree
                ordered_trees_in_future = trees_in_future_searcher.search(working_tree.entity_id, trees_through_years)

                conflicted_fields_checker = conflicted_fields_checker.get_conflicted_links(
                    link_before_update,
                    ordered_trees_in_future
                )

                current_link = link_after_update
                for next_year_tree in ordered_trees_in_future:
                    if next_year_tree.year in conflicted_fields_checker:
                        break  # Do not copy info from year to N+1 because conflict detected
                    cmd = UpdateLinkCommand(
                        parent_node_code=current_link.parent.code,
                        parent_node_year=next_year_tree.year,
                        child_node_code=current_link.child.code,
                        child_node_year=next_year_tree.year,
                        access_condition=current_link.access_condition,
                        is_mandatory=current_link.is_mandatory,
                        block=current_link.block,
                        link_type=current_link.link_type,
                        comment=current_link.comment,
                        comment_english=current_link.comment_english,
                        relative_credits=current_link.relative_credits,
                    )
                    next_year_updated_link = next_year_tree.update_link(cmd)
                    updated_links.append(next_year_updated_link)
                    updated_program_trees.append(next_year_tree)
                    current_link = next_year_updated_link
                if conflicted_fields_checker:
                    first_conflict_year = min(conflicted_fields_checker.keys())
                    working_tree.report.add_warning(
                        report_events.CannotPostponeLinkToNextYearAsConsistencyError(
                            first_conflict_year,
                            conflicted_fields_checker[first_conflict_year]
                        )
                    )
        return updated_links, updated_program_trees

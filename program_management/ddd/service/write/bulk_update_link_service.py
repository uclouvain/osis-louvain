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
from copy import copy
from typing import List

from django.db import transaction

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from education_group.calendar.education_group_switch_calendar import EducationGroupSwitchCalendar
from education_group.ddd.domain.service.conflicted_fields import ConflictedFields
from program_management.ddd.business_types import *
from program_management.ddd.command import BulkUpdateLinkCommand
from program_management.ddd.domain.exception import BulkUpdateLinkException
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.domain.report import Report, ReportIdentity
from program_management.ddd.domain.service.postpone_link import PostponeLink
from program_management.ddd.domain.service.search_program_trees_in_future import SearchProgramTreesInFuture
from program_management.ddd.repositories.report import ReportRepository


@transaction.atomic()
def bulk_update_and_postpone_links(
        cmd: BulkUpdateLinkCommand,
        repository: 'ProgramTreeRepository',
        report_repo: 'ReportRepository'
) -> List['Link']:
    # GIVEN
    working_tree_id = ProgramTreeIdentity(code=cmd.working_tree_code, year=cmd.working_tree_year)
    trees_through_years = repository.search(code=working_tree_id.code)
    working_tree = next(tree for tree in trees_through_years if tree.entity_id == working_tree_id)
    working_tree.report = Report(entity_id=ReportIdentity(transaction_id=cmd.transaction_id))

    # WHEN
    # FIXME :: Used in the view to display success messages...
    #  should be refactored because it's not the responsibility of the ApplicationService
    links_updated = []
    trees_updated = [working_tree]  # Links are updated only in the context of a ProgramTree
    exceptions = dict()
    for update_cmd in cmd.update_link_cmds:
        try:
            link_before_update = copy(working_tree.get_link_from_identity(update_cmd.link_identity))
            link_updated = working_tree.update_link(update_cmd)
            links_updated.append(link_updated)
            updated_links_in_future, update_trees_in_future = PostponeLink.postpone(
                working_tree=working_tree,
                link_before_update=link_before_update,
                link_after_update=link_updated,
                trees_through_years=trees_through_years,
                trees_in_future_searcher=SearchProgramTreesInFuture(),
                conflicted_fields_checker=ConflictedFields(),
                calendar=EducationGroupSwitchCalendar(),
            )
            links_updated += updated_links_in_future
            trees_updated += update_trees_in_future
        except MultipleBusinessExceptions as e:
            exceptions[update_cmd] = e
    if exceptions:
        raise BulkUpdateLinkException(exceptions=exceptions)

    # THEN
    for tree in trees_updated:
        repository.update(tree)

    report_repo.create(working_tree.report)

    return links_updated

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
from program_management.ddd.domain.service.academic_year_search import ExistingAcademicYearSearch
from program_management.ddd.service.write import delete_program_tree_service
from program_management.ddd.business_types import *


@transaction.atomic()
def delete_all_program_tree(cmd: command.DeleteAllProgramTreeCommand) -> List['ProgramTreeIdentity']:
    node_ids = ExistingAcademicYearSearch().search_from_code(group_code=cmd.code)

    program_ids = []
    for node_id in node_ids:
        cmd_delete_program_tree = command.DeleteProgramTreeCommand(code=node_id.code, year=node_id.year)
        program_id_deleted = delete_program_tree_service.delete_program_tree(cmd_delete_program_tree)
        program_ids.append(program_id_deleted)
    return program_ids

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

from osis_common.ddd import interface
from program_management.ddd.business_types import *


class SearchProgramTreesInFuture(interface.DomainService):

    @classmethod
    def search(
            cls,
            working_tree_identity: 'ProgramTreeIdentity',
            trees_through_years: List['ProgramTree']
    ) -> List['ProgramTree']:
        working_year = working_tree_identity.year
        ordered_trees_in_future = list(
            sorted(
                filter(
                    lambda t: t.year > working_year and t.entity_id.code == working_tree_identity.code,
                    trees_through_years
                ),
                key=lambda t: t.year
            )
        )  # type: List['ProgramTree']
        return ordered_trees_in_future

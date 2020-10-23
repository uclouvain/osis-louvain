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
import sys
from typing import Set

from base.ddd.utils import business_validator
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception


class Check2MEndDateGreaterOrEqualToItsFinalities(business_validator.BusinessValidator):
    def __init__(self, tree_version: 'ProgramTreeVersion'):
        self.tree_version = tree_version

    def validate(self, *args, **kwargs):
        if not self.tree_version.get_tree().is_master_2m():
            return

        finalities = self.tree_version.get_tree().get_all_finalities()
        if not finalities:
            return

        finality_with_greatest_end_date = self._get_finality_with_greatest_end_date(finalities)

        if self._is_tree_version_end_year_inferior(finality_with_greatest_end_date):
            raise exception.Program2MEndDateShouldBeGreaterOrEqualThanItsFinalities(finality_with_greatest_end_date)

    def _get_finality_with_greatest_end_date(self, finalities: Set['Node']) -> 'Node':
        return sorted((finality for finality in finalities), key=lambda node: node.end_year or sys.maxsize)[-1]

    def _is_tree_version_end_year_inferior(self, finality: 'Node') -> bool:
        tree_version_end_year = self.tree_version.end_year_of_existence
        return tree_version_end_year and (finality.end_year is None or tree_version_end_year < finality.end_year)

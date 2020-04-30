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
from typing import List, Set

from django.utils.translation import gettext_lazy as _

from base.ddd.utils.business_validator import BusinessValidator
from program_management.ddd.business_types import *


class ReuseOldLearningUnitNodeValidator(BusinessValidator):
    def __init__(
            self,
            tree_to_fill: 'ProgramTree',
            copy_from_node: 'NodeLearningUnitYear',
            existing_nodes_into_year_to_fill: List['NodeLearningUnitYear']
    ):

        years_to_fill = set(n.year for n in existing_nodes_into_year_to_fill)
        if years_to_fill:
            assert len(years_to_fill) == 1, "Should have all nodes of one year only"
            assert tree_to_fill.root_node.year == list(years_to_fill)[0], "Should be the same year than the tree to fill in"

        super(ReuseOldLearningUnitNodeValidator, self).__init__()
        self.copy_from_node = copy_from_node
        self.existing_codes_into_year_to_fill_in = existing_nodes_into_year_to_fill
        self.tree_to_fill = tree_to_fill

    def validate(self):
        if self.copy_from_node.code not in self.existing_acronyms:
            self.add_warning_message(
                _("Learning unit %(learning_unit_year)s does not exist in %(academic_year)s => "
                  "Learning unit is postponed with academic year of %(learning_unit_academic_year)s.") % {
                    "learning_unit_year": self.copy_from_node.code,
                    "academic_year": self.tree_to_fill.root_node.year,
                    "learning_unit_academic_year": self.copy_from_node.academic_year
                }
            )

    @property
    def existing_acronyms(self) -> Set[str]:
        return set(n.code for n in self.existing_codes_into_year_to_fill_in)

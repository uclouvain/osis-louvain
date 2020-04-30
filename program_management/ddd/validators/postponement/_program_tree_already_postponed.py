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

from django.utils.translation import gettext_lazy as _

from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums.education_group_types import MiniTrainingType
from program_management.ddd.business_types import *


# TODO :: unit tests
class ProgramTreeAlreadyPostponedValidator(BusinessValidator):
    def __init__(
            self,
            tree_to_fill_in: 'ProgramTree',
            copy_from_node: 'NodeGroupYear',
            existing_nodes_into_year_to_fill: List['Node']  # TODO :: typing ExistingNodesWithTheirChildren
    ):
        super(ProgramTreeAlreadyPostponedValidator, self).__init__()
        self.copy_from_node = copy_from_node
        self.tree_to_fill_in = tree_to_fill_in
        self.existing_nodes_into_year_to_fill = existing_nodes_into_year_to_fill

    def validate(self):
        # TODO :: supprimer l'utilisation de load_node et réutiliser get_existing_node_next_year
        # TODO :: implémenter le is_empty() qui se base sur les mandatory groups (squelette)
        # TODO :: à merger / réutiliser avec NodeGroupAlreadyPostponedValidator ??
        # To implement from _check_if_already_postponed (program_management/business/group_element_years/postponement
        pass

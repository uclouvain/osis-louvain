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
class EmptyReferenceLinkToPostponeValidator(BusinessValidator):
    def __init__(
            self,
            tree_to_copy: 'ProgramTree',
            link_to_copy: 'Link',
            existing_nodes_into_year_to_fill: List['NodeGroupYear']
    ):
        """
        :param tree_to_copy: Tree to copy into next year.
        :param link_to_copy: Link to copy into next year.
        :param existing_nodes_into_year_to_fill: List of nodes WITH THEIR CHILDREN.
        """
        super(EmptyReferenceLinkToPostponeValidator, self).__init__()
        self.link_to_copy = link_to_copy
        self.tree_to_fill_in = tree_to_copy
        self.existing_nodes_into_year_to_fill = existing_nodes_into_year_to_fill

    def validate(self):
        # To implement from ReferenceLinkEmptyWarning (program_management/business/group_element_years/postponement)
        raise NotImplementedError()

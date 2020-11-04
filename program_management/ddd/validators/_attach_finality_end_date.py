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
import sys
from typing import List

from base.ddd.utils import business_validator
from base.models.enums.education_group_types import TrainingType
from base.utils.constants import INFINITE_VALUE
from program_management.ddd.business_types import *
from program_management.ddd.domain.exception import CannotAttachFinalitiesWithGreaterEndDateThanProgram2M


class AttachFinalityEndDateValidator(business_validator.BusinessValidator):
    """
    In context of 2M, when we add a finality [or group which contains finality], we must ensure that
    the end date of all 2M is greater or equals of all finalities.
    """

    def __init__(self, tree_version_2m: 'ProgramTreeVersion', tree_from_node_to_add: 'ProgramTree', *args):
        super(AttachFinalityEndDateValidator, self).__init__()
        if tree_from_node_to_add.root_node.is_finality() or tree_from_node_to_add.get_all_finalities():
            assert_msg = "To use correctly this validator, make sure the ProgramTree root is of type 2M"
            assert tree_version_2m.tree.root_node.node_type in TrainingType.root_master_2m_types_enum(), assert_msg
        self.tree_from_node_to_add = tree_from_node_to_add
        self.node_to_add = tree_from_node_to_add.root_node
        self.tree_version_2m = tree_version_2m

    def validate(self):
        if self.node_to_add.is_finality() or self.tree_from_node_to_add.get_all_finalities():
            inconsistent_finalities = self._get_finalities_where_end_date_gt_root_end_date()
            if inconsistent_finalities:
                raise CannotAttachFinalitiesWithGreaterEndDateThanProgram2M(
                    self.tree_version_2m.tree.root_node,
                    inconsistent_finalities
                )

    def _get_finalities_where_end_date_gt_root_end_date(self) -> List['Node']:
        root_end_year = self.tree_version_2m.tree.root_node.end_year or INFINITE_VALUE
        return [
            finality for finality in self.tree_from_node_to_add.get_all_finalities()
            if (finality.end_year or INFINITE_VALUE) > root_end_year
        ]

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

from django.utils.translation import gettext_lazy as _

from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums.education_group_types import MiniTrainingType
from program_management.ddd.business_types import *
from program_management.ddd.repositories import load_node


# TODO :: unit tests
class NodeGroupAlreadyPostponedValidator(BusinessValidator):
    def __init__(self, tree_to_fill_in: 'ProgramTree', copy_from_node: 'NodeGroupYear'):
        super(NodeGroupAlreadyPostponedValidator, self).__init__()
        self.copy_from_node = copy_from_node
        self.tree_to_fill_in = tree_to_fill_in

    def validate(self):
        year_of_tree_to_fill = self.tree_to_fill_in.root_node.year
        existing_node = load_node.load_same_node_by_year(self.copy_from_node, year_of_tree_to_fill)
        if existing_node \
                and not self.copy_from_node.is_training() \
                and self.copy_from_node.node_type.name not in MiniTrainingType.to_postpone():
            self.add_warning_message(
                _("%(node_code)s has already been copied in %(academic_year)s in another program. "
                  "It may have been already modified.") % {
                    "node_code": self.copy_from_node.code,
                    "academic_year": self.tree_to_fill_in.root_node.academic_year
                }
            )

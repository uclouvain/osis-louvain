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

from django.utils.translation import ngettext

from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums.education_group_types import TrainingType
from program_management.ddd.business_types import *
from program_management.ddd.domain import program_tree


# Implemented from _check_end_year_constraints_on_2m
class AttachFinalityEndDateValidator(BusinessValidator):
    """
    In context of 2M, when we add a finality [or group which contains finality], we must ensure that
    the end date of all 2M is greater or equals of all finalities.
    """

    def __init__(self, tree_2m: 'ProgramTree', tree_from_node_to_add: 'ProgramTree', *args):
        super(AttachFinalityEndDateValidator, self).__init__()
        msg = "This validator need the children of the node to add. Please load the complete Tree from the Node to Add"
        assert isinstance(tree_from_node_to_add, program_tree.ProgramTree), msg
        if tree_from_node_to_add.root_node.is_finality() or tree_from_node_to_add.get_all_finalities():
            assert_error_msg = "To use correctly this validator, make sure the ProgramTree root is of type 2M"
            assert tree_2m.root_node.node_type in TrainingType.root_master_2m_types_enum(), assert_error_msg
        self.tree_from_node_to_add = tree_from_node_to_add
        self.node_to_add = tree_from_node_to_add.root_node
        self.tree_2m = tree_2m

    def validate(self):
        if self.node_to_add.is_finality() or self.tree_from_node_to_add.get_all_finalities():
            inconsistent_nodes = self._get_codes_where_end_date_gte_root_end_date()
            if inconsistent_nodes:
                self.add_error_message(
                    ngettext(
                        "Finality \"%(code)s\" has an end date greater than %(root_code)s program.",
                        "Finalities \"%(code)s\" have an end date greater than %(root_code)s program.",
                        len(inconsistent_nodes)
                    ) % {
                        "code": ', '.join(inconsistent_nodes),
                        "root_code": self.tree_2m.root_node.code
                    }
                )

    def _get_codes_where_end_date_gte_root_end_date(self):
        root_end_date = self.tree_2m.root_node.end_date
        return [
            finality.code for finality in self.tree_from_node_to_add.get_all_finalities()
            if all([finality.end_date, root_end_date]) and finality.end_date > root_end_date
        ]

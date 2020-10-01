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

from django.utils.translation import ngettext

import osis_common.ddd.interface
from base.ddd.utils import business_validator
from base.models.enums.education_group_types import TrainingType
from program_management import formatter
from program_management.ddd.business_types import *
from program_management.ddd.domain.service import identity_search


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
            inconsistent_nodes = self._get_finality_nodes_where_end_date_gte_root_end_date()
            if inconsistent_nodes:
                raise osis_common.ddd.interface.BusinessExceptions(
                    [ngettext(
                        "Finality \"%(acronym)s\" has an end date greater than %(root_acronym)s program.",
                        "Finalities \"%(acronym)s\" have an end date greater than %(root_acronym)s program.",
                        len(inconsistent_nodes)
                    ) % {
                        "acronym": ', '.join(self._display_inconsistent_nodes(inconsistent_nodes)),
                        "root_acronym": formatter.format_program_tree_version_identity(self.tree_version_2m.entity_id)
                    }]
                )

    def _get_finality_nodes_where_end_date_gte_root_end_date(self) -> List['Node']:
        root_end_year = self.tree_version_2m.tree.root_node.end_year
        return [
            finality for finality in self.tree_from_node_to_add.get_all_finalities()
            if (all([finality.end_year, root_end_year]) and finality.end_year > root_end_year) or
            (finality.end_year is None and root_end_year is not None)
        ]

    def _display_inconsistent_nodes(self, nodes: List['Node']) -> List[str]:
        node_identities = [node.entity_id for node in nodes]
        version_identities = identity_search.ProgramTreeVersionIdentitySearch.get_from_node_identities(node_identities)
        return [formatter.format_program_tree_version_identity(version_identity)
                for version_identity in version_identities]

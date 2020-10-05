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
from typing import List, Iterable

from django.utils.translation import ngettext

from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums.education_group_types import MiniTrainingType, TrainingType
from program_management import formatter
from program_management.ddd.business_types import *
from program_management.ddd.domain.service import identity_search


class AttachOptionsValidator(BusinessValidator):
    """
    In context of MA/MD/MS when we add an option [or group which contains options],
    this options must exist in parent context (2m)
    """

    def __init__(
            self,
            tree_version_2m: 'ProgramTreeVersion',
            tree_from_node_to_add: 'ProgramTree',
            node_to_paste_to: 'Node',
            *args
    ):
        super(AttachOptionsValidator, self).__init__()
        if tree_from_node_to_add.root_node.is_finality() or tree_from_node_to_add.get_all_finalities():
            assert_msg = "To use correctly this validator, make sure the ProgramTree root is of type 2M"
            assert tree_version_2m.tree.root_node.node_type in TrainingType.root_master_2m_types_enum(), assert_msg
        self.tree_from_node_to_add = tree_from_node_to_add
        self.node_to_add = tree_from_node_to_add.root_node
        self.node_to_paste_to = node_to_paste_to
        self.tree_version_2m = tree_version_2m

    def get_options_to_attach(self):
        options = self.tree_from_node_to_add.root_node.get_all_children_as_nodes(take_only={MiniTrainingType.OPTION})
        if self.node_to_add.is_option():
            options.add(self.tree_from_node_to_add.root_node)
        return options

    def validate(self):
        if not(self._is_node_to_paste_to_inside_a_finality() or self._is_tree_to_add_a_finality()):
            return

        options_to_attach = self.get_options_to_attach()
        if options_to_attach:
            options_from_2m_option_list = self.tree_version_2m.tree.get_2m_option_list()
            options_to_attach_not_present_in_2m_option_list = options_to_attach - options_from_2m_option_list
            if options_to_attach_not_present_in_2m_option_list:
                self.add_error_message(
                    ngettext(
                        "Option \"%(code)s\" must be present in %(root_code)s program.",
                        "Options \"%(code)s\" must be present in %(root_code)s program.",
                        len(options_to_attach_not_present_in_2m_option_list)
                    ) % {
                        "code": ', '.join(
                            self._display_inconsistent_nodes(options_to_attach_not_present_in_2m_option_list)
                        ),
                        "root_code": formatter.format_program_tree_version_identity(self.tree_version_2m.entity_id)
                    }
                )

    def _display_inconsistent_nodes(self, nodes: Iterable['Node']) -> List[str]:
        node_identities = [node.entity_id for node in nodes]
        version_identities = identity_search.ProgramTreeVersionIdentitySearch.get_from_node_identities(node_identities)
        return [formatter.format_program_tree_version_identity(version_identity)
                for version_identity in version_identities]

    def _is_node_to_paste_to_inside_a_finality(self) -> bool:
        finalities = self.tree_version_2m.get_tree().root_node.get_finality_list()
        nodes_inside_finalities = finalities.copy()
        for finality in finalities:
            nodes_inside_finalities |= set(finality.children_as_nodes)
        return self.node_to_paste_to in nodes_inside_finalities

    def _is_tree_to_add_a_finality(self):
        return self.tree_from_node_to_add.root_node.is_finality()

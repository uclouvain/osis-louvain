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

    def __init__(self, tree_version_2m: 'ProgramTreeVersion', tree_from_node_to_add: 'ProgramTree', *args):
        super(AttachOptionsValidator, self).__init__()
        if tree_from_node_to_add.root_node.is_finality() or tree_from_node_to_add.get_all_finalities():
            assert_msg = "To use correctly this validator, make sure the ProgramTree root is of type 2M"
            assert tree_version_2m.tree.root_node.node_type in TrainingType.root_master_2m_types_enum(), assert_msg
        self.tree_from_node_to_add = tree_from_node_to_add
        self.node_to_add = tree_from_node_to_add.root_node
        self.tree_version_2m = tree_version_2m

    def get_options_from_finalities(self):
        options_from_finalities = set()
        for finality in self.tree_from_node_to_add.get_all_finalities():
            options_from_finalities |= finality.get_all_children_as_nodes(take_only={MiniTrainingType.OPTION})
        if self.node_to_add.is_finality():
            options_from_finalities |= self.node_to_add.get_all_children_as_nodes(
                take_only={MiniTrainingType.OPTION}
            )
        return options_from_finalities

    def validate(self):
        options_from_finalities = self.get_options_from_finalities()
        if options_from_finalities:
            options_from_2m = self.tree_version_2m.tree.root_node.get_all_children_as_nodes(
                take_only={MiniTrainingType.OPTION},
                ignore_children_from=set(TrainingType.finality_types_enum())
            )
            missing_options = options_from_finalities - options_from_2m
            if missing_options:
                self.add_error_message(
                    ngettext(
                        "Option \"%(code)s\" must be present in %(root_code)s program.",
                        "Options \"%(code)s\" must be present in %(root_code)s program.",
                        len(missing_options)
                    ) % {
                        "code": ', '.join(self._display_inconsistent_nodes(missing_options)),
                        "root_code": formatter.format_program_tree_version_identity(self.tree_version_2m.entity_id)
                    }
                )

    def _display_inconsistent_nodes(self, nodes: Iterable['Node']) -> List[str]:
        node_identities = [node.entity_id for node in nodes]
        version_identities = identity_search.ProgramTreeVersionIdentitySearch.get_from_node_identities(node_identities)
        return [formatter.format_program_tree_version_identity(version_identity)
                for version_identity in version_identities]

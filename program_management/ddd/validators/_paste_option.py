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
from program_management.ddd.domain.exception import CannotAttachOptionIfNotPresentIn2MOptionListException
from program_management.ddd.domain.service import identity_search


class PasteOptionsValidator(BusinessValidator):
    """
    In context of MA/MD/MS when we add an option [or group which contains options],
    this options must exist in parent context (2m)
    """

    def __init__(
            self,
            program_tree_repository: 'ProgramTreeRepository',
            tree_from_node_to_paste: 'ProgramTree',
            node_to_paste_to: 'NodeGroupYear',
            trees_2m: List['ProgramTree']
    ):
        super(PasteOptionsValidator, self).__init__()
        assert_msg = "To use correctly this validator, make sure the ProgramTree root is of type 2M"
        for tree_2m in trees_2m:
            assert tree_2m.root_node.node_type in TrainingType.root_master_2m_types_enum(), assert_msg
        self.program_tree_repository = program_tree_repository
        self.tree_from_node_to_paste = tree_from_node_to_paste
        self.node_to_paste = self.tree_from_node_to_paste.root_node
        self.node_to_paste_to = node_to_paste_to
        self.trees_2m = trees_2m

    def get_options_to_paste(self):
        options = self.tree_from_node_to_paste.root_node.get_all_children_as_nodes(take_only={MiniTrainingType.OPTION})
        if self.node_to_paste.is_option():
            options.add(self.node_to_paste)
        return options

    def validate(self):
        options_to_attach = self.get_options_to_paste()
        if options_to_attach:
            for tree_2m in self.trees_2m:
                if self._is_node_to_paste_a_finality() or self._is_node_to_paste_to_inside_a_finality(tree_2m):
                    options_from_2m_option_list = tree_2m.get_2m_option_list()
                    options_to_attach_not_present_in_2m_option_list = options_to_attach - options_from_2m_option_list
                    if options_to_attach_not_present_in_2m_option_list:
                        raise CannotAttachOptionIfNotPresentIn2MOptionListException(
                            tree_2m.root_node,
                            options_to_attach_not_present_in_2m_option_list
                        )

    def _is_node_to_paste_to_inside_a_finality(self, tree_2m: 'ProgramTree') -> bool:
        finalities = tree_2m.root_node.get_finality_list()
        nodes_inside_finalities = finalities.copy()
        for finality in finalities:
            nodes_inside_finalities |= set(finality.children_as_nodes)
        return self.node_to_paste_to in nodes_inside_finalities

    def _is_node_to_paste_a_finality(self):
        return self.node_to_paste.is_finality()

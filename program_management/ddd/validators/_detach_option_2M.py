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
from collections import Counter

from django.utils.translation import ngettext

import osis_common.ddd.interface
from base.ddd.utils import business_validator
from program_management.ddd.business_types import *


class DetachOptionValidator(business_validator.BusinessValidator):
    """
    In context of MA/MD/MS when we add an option [or group which contains options],
    this options must exist in parent context (2m)
    """

    def __init__(
            self,
            working_tree: 'ProgramTree',
            path_to_node_to_detach: 'Path',
            tree_repository: 'ProgramTreeRepository'
    ):
        super(DetachOptionValidator, self).__init__()
        self.working_tree = working_tree
        self.path_to_node_to_detach = path_to_node_to_detach
        self.node_to_detach = working_tree.get_node(path_to_node_to_detach)
        self.tree_repository = tree_repository

    def get_options_to_detach(self):
        result = []
        if self.node_to_detach.is_option():
            result.append(self.node_to_detach)
        result += self.node_to_detach.get_option_list()
        return result

    def validate(self):
        trees_2m = [
            tree for tree in self.tree_repository.search_from_children(node_ids=[self.node_to_detach.entity_id])
            if tree.is_master_2m()
        ]

        error_messages = []
        options_to_detach = self.get_options_to_detach()
        if options_to_detach and not self._is_inside_finality():
            for tree_2m in trees_2m:
                counter_options = Counter(tree_2m.get_2m_option_list())
                counter_options.subtract(options_to_detach)
                options_to_check = [opt for opt, count in counter_options.items() if count == 0]
                if not options_to_check:
                    continue
                for finality in tree_2m.get_all_finalities():
                    options_to_detach_used_in_finality = set(options_to_detach) & set(finality.get_option_list())
                    if options_to_detach_used_in_finality:
                        error_messages.append(
                            ngettext(
                                "Option \"%(acronym)s\" cannot be detach because it is contained in"
                                " %(finality_acronym)s program.",
                                "Options \"%(acronym)s\" cannot be detach because they are contained in"
                                " %(finality_acronym)s program.",
                                len(options_to_detach_used_in_finality)
                            ) % {
                                "acronym": ', '.join(option.title for option in options_to_detach_used_in_finality),
                                "finality_acronym": finality.title
                            }
                        )
        if error_messages:
            raise osis_common.ddd.interface.BusinessExceptions(error_messages)

    def _is_inside_finality(self):
        parents = self.working_tree.get_parents(self.path_to_node_to_detach)
        return any(p.is_finality() for p in parents)

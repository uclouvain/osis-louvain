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
from typing import List

from base.ddd.utils import business_validator
from program_management.ddd.business_types import *
from program_management.ddd.domain.exception import CannotDetachOptionsException


class DetachOptionValidator(business_validator.BusinessValidator):

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
        self.options_to_detach = self._get_options_to_detach()

    def validate(self):
        parent = self.working_tree.get_node(self._extract_parent_path(self.path_to_node_to_detach))
        trees_2m = self._get_trees_2m_containing_parent(parent)

        if self.options_to_detach and not self._is_inside_finality():
            for tree_2m in trees_2m:
                options_to_check = self._get_options_to_check_by_tree(tree_2m)
                if not options_to_check:
                    continue
                self._validate_option_usage_in_finalities(tree_2m)

    def _validate_option_usage_in_finalities(self, tree_2m: 'ProgramTree'):
        for finality in tree_2m.get_all_finalities():
            options_to_detach_used_in_finality = set(self.options_to_detach) & set(finality.get_option_list())
            if options_to_detach_used_in_finality:
                raise CannotDetachOptionsException(finality, options_to_detach_used_in_finality)

    def _extract_parent_path(self, path_to_node: str) -> str:
        return path_to_node.rsplit('|', 1)[0]

    def _get_options_to_check_by_tree(self, tree_2m: 'ProgramTree') -> List['Node']:
        counter_options = Counter(tree_2m.get_2m_option_list())
        counter_options.subtract(self.options_to_detach)
        options_to_check = [opt for opt, count in counter_options.items() if count == 0]
        return options_to_check

    def _get_trees_2m_containing_parent(self, parent: 'Node') -> List['ProgramTree']:
        return [
            tree for tree in self.tree_repository.search_from_children(node_ids=[parent.entity_id])
            if tree.is_master_2m()
        ]

    def _get_options_to_detach(self) -> List['Node']:
        result = []
        if self.node_to_detach.is_option():
            result.append(self.node_to_detach)
        result += self.node_to_detach.get_option_list()
        return result

    def _is_inside_finality(self) -> bool:
        parents = self.working_tree.get_parents(self.path_to_node_to_detach)
        return self.node_to_detach.is_finality() or any(p.is_finality() for p in parents)

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

from base.ddd.utils import business_validator
from program_management.ddd.domain import exception


class MatchVersionValidator(business_validator.BusinessValidator):

    def __init__(
            self,
            node_to_paste_to: 'Node',
            node_to_add: 'Node',
            tree_repository: 'ProgramTreeRepository',
            tree_version_repository: 'ProgramTreeVersionRepository'
    ):
        super(MatchVersionValidator, self).__init__()

        self.node_to_paste_to = node_to_paste_to
        self.node_to_add = node_to_add
        self.tree_repository = tree_repository
        self.tree_version_repository = tree_version_repository

    def validate(self):
        if self.node_to_add.is_training():
            child_version = self._get_program_tree_version(self.node_to_add)

            parent_versions = self._get_all_program_tree_version_using_node(self.node_to_paste_to)
            if not self.node_to_paste_to.is_group():
                parent_versions.append(self._get_program_tree_version(self.node_to_paste_to))

            version_mismatched = [
                parent_version.entity_id for parent_version in parent_versions
                if parent_version.version_name != child_version.version_name
            ]
            if version_mismatched:
                raise exception.ProgramTreeVersionMismatch(
                    self.node_to_add,
                    child_version.entity_id,
                    self.node_to_paste_to,
                    version_mismatched,
                )

    def _get_program_tree_version(self, node: 'Node') -> 'ProgramTreeVersion':
        from program_management.ddd.domain.program_tree import ProgramTreeIdentity

        program_tree_identity = ProgramTreeIdentity(code=node.entity_id.code, year=node.entity_id.year)
        tree = self.tree_repository.get(program_tree_identity)
        return self.tree_version_repository.search_versions_from_trees([tree])[0]

    def _get_all_program_tree_version_using_node(self, node: 'Node') -> List['ProgramTreeVersion']:
        program_trees = self.tree_repository.search_from_children([node.entity_id])
        return self.tree_version_repository.search_versions_from_trees(program_trees)

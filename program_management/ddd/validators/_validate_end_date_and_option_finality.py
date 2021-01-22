# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import osis_common.ddd.interface
from base.ddd.utils import business_validator
from base.models.enums.education_group_types import MiniTrainingType
from program_management.ddd.business_types import *
from program_management.ddd.validators import _end_date_between_finalities_and_masters
from program_management.ddd.validators import _paste_option
from program_management.ddd.domain.service import identity_search


class ValidateFinalitiesEndDateAndOptions(business_validator.BusinessValidator):
    def __init__(
            self,
            node_to_paste_to: 'Node',
            node_to_paste: 'Node',
            tree_repository: 'ProgramTreeRepository',
    ):
        super().__init__()
        self.node_to_paste = node_to_paste
        self.tree_repository = tree_repository
        self.node_to_paste_to = node_to_paste_to

    def validate(self, *args, **kwargs):
        tree_from_node_to_paste = self._get_tree_of_node_to_paste()

        if self.has_finalities(tree_from_node_to_paste) or self.has_options(tree_from_node_to_paste):
            trees_2m = [
                tree for tree in self.tree_repository.search_from_children([self.node_to_paste_to.entity_id])
                if tree.is_master_2m()
            ]
            _end_date_between_finalities_and_masters.CheckEndDateBetweenFinalitiesAndMasters2M(
                updated_tree=tree_from_node_to_paste,
                program_tree_repository=self.tree_repository,
                trees_2m=trees_2m,
            ).validate()
            _paste_option.PasteOptionsValidator(
                program_tree_repository=self.tree_repository,
                tree_from_node_to_paste=tree_from_node_to_paste,
                node_to_paste_to=self.node_to_paste_to,
                trees_2m=trees_2m,
            ).validate()

    def has_finalities(self, tree_from_node_to_paste):
        return tree_from_node_to_paste.get_all_finalities() or tree_from_node_to_paste.root_node.is_finality()

    def has_options(self, tree_from_node_to_paste):
        return tree_from_node_to_paste.root_node.get_all_children_as_nodes(take_only={MiniTrainingType.OPTION}) \
            or self.node_to_paste.is_option()

    def _get_tree_of_node_to_paste(self):
        tree_identity = identity_search.ProgramTreeIdentitySearch.get_from_node_identity(self.node_to_paste.entity_id)
        return self.tree_repository.get(tree_identity)

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
from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums.link_type import LinkTypes
from program_management.ddd.business_types import *
from program_management.ddd.validators._authorized_relationship import PasteAuthorizedRelationshipValidator


class ValidateAuthorizedRelationshipForAllTrees(BusinessValidator):
    def __init__(
            self,
            tree: 'ProgramTree',
            node_to_paste: 'Node',
            path: 'Path',
            tree_repository: 'ProgramTreeRepository'
    ) -> None:
        super().__init__()
        self.tree = tree
        self.node_to_paste = node_to_paste
        self.path = path
        self.tree_repository = tree_repository

    def validate(self, *args, **kwargs):
        child_node = self.tree.get_node(self.path)
        trees = self.tree_repository.search_from_children([child_node.entity_id], link_type=LinkTypes.REFERENCE)
        messages = []
        for tree in trees:
            for parent_from_reference_link in tree.get_parents_using_node_as_reference(child_node):
                validator = PasteAuthorizedRelationshipValidator(tree, self.node_to_paste, parent_from_reference_link)
                if not validator.is_valid():
                    for msg in validator.error_messages:
                        messages.append(msg.message)

        if messages:
            raise osis_common.ddd.interface.BusinessExceptions(messages)

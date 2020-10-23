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
from typing import Optional, Set

from django.utils.translation import gettext_lazy as _

import osis_common.ddd.interface
from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums import education_group_types
from base.models.enums.link_type import LinkTypes
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception
from program_management.ddd.domain.node import Node
from program_management.models.enums.node_type import NodeType


class AuthorizedLinkTypeValidator(BusinessValidator):
    def __init__(self, tree: 'ProgramTree', node_to_add: Node, link_type: Optional[LinkTypes]):
        self.tree = tree
        self.parent_node = tree.root_node
        self.node_to_add = node_to_add
        self.link_type = link_type

        super().__init__()

    def validate(self, *args, **kwargs):
        if self.node_to_add.node_type == NodeType.LEARNING_UNIT and self.link_type == LinkTypes.REFERENCE:
            raise exception.ReferenceLinkNotAllowedWithLearningUnitException(self.node_to_add)

        elif self._is_child_a_minor_major_or_option_inside_a_list_minor_major_option_choice_parent() and \
                self.link_type != LinkTypes.REFERENCE:
            raise exception.LinkShouldBeReferenceException(parent_node=self.parent_node, child_node=self.node_to_add)

        elif self.link_type == LinkTypes.REFERENCE and not self._is_node_to_add_a_valid_reference_link():
            raise exception.ReferenceLinkNotAllowedException(
                parent_node=self.parent_node,
                child_node=self.node_to_add,
                reference_childrens=self._get_not_authorized_referenced_children()
            )

    def _is_child_a_minor_major_or_option_inside_a_list_minor_major_option_choice_parent(self):
        return self.parent_node.node_type in education_group_types.GroupType.minor_major_list_choice_enums() and \
               self.node_to_add.node_type in education_group_types.MiniTrainingType

    def _is_node_to_add_a_valid_reference_link(self):
        return not bool(self._get_not_authorized_referenced_children()) or \
               self._is_child_a_minor_major_or_option_inside_a_list_minor_major_option_choice_parent()

    def _get_not_authorized_referenced_children(self) -> Set['Node']:
        children_of_node_to_add = self.node_to_add.children_as_nodes
        return {
            child_node
            for child_node in children_of_node_to_add
            if not self.tree.authorized_relationships.is_authorized(
                parent_type=self.parent_node.node_type,
                child_type=child_node.node_type
            )
        }

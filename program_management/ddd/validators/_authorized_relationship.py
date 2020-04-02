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

from django.utils.translation import gettext as _

from base.ddd.utils.business_validator import BusinessValidator
from program_management.ddd.business_types import *


# Implemented from CheckAuthorizedRelationship (management.py)
class AttachAuthorizedRelationshipValidator(BusinessValidator):
    def __init__(self, tree: 'ProgramTree', node_to_add: 'Node', position_to_add: 'Node'):
        super(AttachAuthorizedRelationshipValidator, self).__init__()
        self.tree = tree
        self.node_to_add = node_to_add
        self.parent = position_to_add
        self.auth_relations = tree.authorized_relationships

    def validate(self):
        if not self.auth_relations.is_authorized(self.parent.node_type, self.node_to_add.node_type):
            self.add_error_message(
                _("You cannot add \"%(child_types)s\" to \"%(parent)s\" (type \"%(parent_type)s\")") % {
                    'child_types': self.node_to_add.node_type.value,
                    'parent': self.parent,
                    'parent_type': self.parent.node_type.value,
                }
            )
        if self.is_maximum_children_types_reached(self.parent, self.node_to_add):
            self.add_error_message(
                _("The parent must have at least one child of type(s) \"%(types)s\".") % {
                    "types": str(self.auth_relations.get_authorized_children_types(self.parent.node_type))
                }
            )

    def is_maximum_children_types_reached(self, parent_node: 'Node', child_node: 'Node'):
        if not self.auth_relations.is_authorized(parent_node.node_type, child_node.node_type):
            return False
        counter = Counter(parent_node.get_children_types(include_nodes_used_as_reference=True))
        current_count = counter[child_node.node_type]
        relation = self.auth_relations.get_authorized_relationship(parent_node.node_type, child_node.node_type)
        return current_count == relation.max_count_authorized


# Implemented from CheckAuthorizedRelationship (management.py)
class DetachAuthorizedRelationshipValidator(BusinessValidator):
    def __init__(self, tree: 'ProgramTree', node_to_add: 'Node', position_to_add: 'Node'):
        super(DetachAuthorizedRelationshipValidator, self).__init__()
        self.tree = tree
        self.node_to_add = node_to_add
        self.parent = position_to_add
        self.auth_relations = tree.authorized_relationships

    def validate(self):
        if self.is_minimum_children_types_reached(self.parent, self.node_to_add):
            self.add_error_message(
                _("The number of children of type(s) \"%(child_types)s\" for \"%(parent)s\" "
                  "has already reached the limit.") % {
                    'child_types': self.node_to_add.node_type.value,
                    'parent': self.parent
                }
            )

    def is_minimum_children_types_reached(self, parent_node: 'Node', child_node: 'Node'):
        if not self.auth_relations.is_authorized(parent_node.node_type, child_node.node_type):
            return False
        counter = Counter(parent_node.get_children_types(include_nodes_used_as_reference=True))
        current_count = counter[child_node.node_type]
        relation = self.auth_relations.get_authorized_relationship(parent_node.node_type, child_node.node_type)
        return current_count == relation.min_count_authorized


class AuthorizedRelationshipLearningUnitValidator(BusinessValidator):
    def validate(self):
        pass  # cf. AttachLearningUnitYearStrategy.id_valid

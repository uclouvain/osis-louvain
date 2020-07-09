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

from django.utils.translation import gettext_lazy as _

from program_management.ddd.business_types import *
from base.ddd.utils.business_validator import BusinessValidator


# Implemented from GroupElementYear._check_same_academic_year_parent_child_branch
from program_management.models.enums.node_type import NodeType


class HasOrIsPrerequisiteValidator(BusinessValidator):

    def __init__(self, tree: 'ProgramTree', node_to_detach: 'NodeLearningUnitYear', path: 'Path'):
        super(HasOrIsPrerequisiteValidator, self).__init__()
        self.node_to_detach = node_to_detach
        self.tree = tree

    def validate(self):
        if self.node_to_detach.is_prerequisite or self.node_to_detach.has_prerequisite:
            self.add_error_message(
                _("Cannot detach due to prerequisites.")
            )


class IsPrerequisiteValidator(BusinessValidator):

    def __init__(self, tree: 'ProgramTree', node_to_detach: 'Node'):
        super(IsPrerequisiteValidator, self).__init__()
        self.node_to_detach = node_to_detach
        self.tree = tree

    def validate(self):
        nodes_that_are_prerequisites = self._get_nodes_that_are_prerequisite(self.node_to_detach)
        if nodes_that_are_prerequisites:
            codes_that_are_prerequisite = [node.code for node in nodes_that_are_prerequisites]
            if self.node_to_detach.is_learning_unit():
                self.add_error_message(
                    _("Cannot detach learning unit %(acronym)s as it has a prerequisite or it is a prerequisite.") % {
                        "acronym": self.node_to_detach.code
                    }
                )
            else:
                self.add_error_message(
                    _("Cannot detach education group year %(acronym)s as the following learning units "
                      "are prerequisite in %(formation)s: %(learning_units)s") % {
                        "acronym": self.node_to_detach.title,
                        "formation": self.tree.root_node.title,
                        "learning_units": ", ".join(codes_that_are_prerequisite)
                    }
                )

    def _get_nodes_that_are_prerequisite(self, search_under_node: 'Node'):
        nodes_that_are_prerequisites = []
        learning_units_children = search_under_node.get_all_children_as_learning_unit_nodes()
        if search_under_node.is_learning_unit() and search_under_node.is_prerequisite:
            nodes_that_are_prerequisites.append(search_under_node)
        nodes_that_are_prerequisites += [
            n for n in learning_units_children
            if n.is_prerequisite and not self._is_reused_in_tree(n)
        ]
        return sorted(nodes_that_are_prerequisites, key=lambda n: n.code)

    def _is_reused_in_tree(self, node_to_detach: 'Node') -> bool:
        return self.tree.count_usage(node_to_detach) > 1


class HasPrerequisiteValidator(BusinessValidator):

    def __init__(self, tree: 'ProgramTree', node_to_detach: 'Node'):
        super(HasPrerequisiteValidator, self).__init__()
        self.node_to_detach = node_to_detach
        self.tree = tree

    def validate(self):
        nodes_that_has_prerequisites = self._get_nodes_that_has_prerequisite()
        if nodes_that_has_prerequisites:
            codes_that_have_prerequisites = [node.code for node in nodes_that_has_prerequisites]
            self.add_warning_message(
                _("The prerequisites for the following learning units contained in education group year "
                  "%(acronym)s will we deleted: %(learning_units)s") % {
                    "acronym": self.tree.root_node.title,
                    "learning_units": ", ".join(codes_that_have_prerequisites)
                }
            )

    def _get_nodes_that_has_prerequisite(self):
        search_under_node = self.node_to_detach
        nodes_that_has_prerequisites = []
        learning_units_children = search_under_node.get_all_children_as_learning_unit_nodes()
        if search_under_node.is_learning_unit() and search_under_node.has_prerequisite:
            nodes_that_has_prerequisites.append(search_under_node)
        nodes_that_has_prerequisites += [
            n for n in learning_units_children
            if n.has_prerequisite
        ]
        return nodes_that_has_prerequisites

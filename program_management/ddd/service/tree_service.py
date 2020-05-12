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

from program_management.ddd.business_types import *
from program_management.ddd.repositories import load_tree


def search_trees_using_node(node_to_detach: 'Node'):
    node_id = node_to_detach.pk
    if node_to_detach.is_learning_unit():
        trees = load_tree.load_trees_from_children(child_branch_ids=None, child_leaf_ids=[node_id])
    else:
        trees = load_tree.load_trees_from_children(child_branch_ids=[node_id], child_leaf_ids=None)
    return trees

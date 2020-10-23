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
from typing import Set, List

import program_management.ddd
from program_management.ddd.business_types import *
from program_management.ddd.service.read.search_all_versions_from_root_nodes import search_all_versions_from_root_nodes


def get_program_tree_version_for_tree(tree_nodes: Set['Node']) -> List['ProgramTreeVersion']:
    commands = [
        program_management.ddd.command.SearchAllVersionsFromRootNodesCommand(code=node.code,
                                                                             year=node.year) for node in tree_nodes
    ]
    return search_all_versions_from_root_nodes(commands)

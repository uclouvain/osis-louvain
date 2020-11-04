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
from typing import List, Tuple

from django.urls import reverse

from program_management.ddd.business_types import *
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository


# FIXME :: Create a service to return List['ProgramTreeVersionIdentity']
def get_tree_versions_choices(
        node_identity: 'NodeIdentity',
        active_view_name: str
) -> List[Tuple[str, 'ProgramTreeVersionIdentity']]:

    tree_versions = ProgramTreeVersionRepository.search_all_versions_from_root_node(node_identity)

    choices = []
    for tree_version in tree_versions:
        node_identity = NodeIdentitySearch().get_from_program_tree_identity(tree_version.program_tree_identity)
        choices.append(
            (
                _get_href(node_identity, active_view_name),
                tree_version.entity_id,
            )
        )

    return _get_ordered_version_choices(choices)


def _get_href(node_identity: 'NodeIdentity', active_view_name: str) -> str:
    return reverse(active_view_name, args=[node_identity.year, node_identity.code])


def _get_ordered_version_choices(versions_choices):
    return sorted(versions_choices,
                  key=lambda version_choice: (version_choice[1].version_name, version_choice[1].is_transition)
                  )

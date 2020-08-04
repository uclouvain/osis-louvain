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
from program_management.ddd.domain.service.academic_year_search import ExistingAcademicYearSearch
from program_management.ddd.domain.service.element_id_search import ElementIdByYearSearch


# FIXME :: Create a service to return List['NodeIdentity']
def get_academic_year_choices(
        node_identity: 'NodeIdentity',
        path: 'Path',
        active_view_name: str,
) -> List[Tuple[str, int]]:
    element_ids = [int(element_id) for element_id in path.split('|')]
    map_element_id_by_year = ElementIdByYearSearch().search_from_element_ids(
        element_ids=element_ids,
    )
    node_ids = ExistingAcademicYearSearch().search_from_code(node_identity.code)

    return [
        (
            _get_href(
                node_identity=node_id,
                path='|'.join(str(map_element_id_by_year[elem_id][node_id.year]) for elem_id in element_ids),
                active_view_name=active_view_name,
            ),
            node_id.year
        )
        for node_id in node_ids
    ]


def _get_href(node_identity: 'NodeIdentity', path: 'Path', active_view_name: str) -> str:
    return reverse(active_view_name, args=[node_identity.year, node_identity.code]) + "?path=%s" % path

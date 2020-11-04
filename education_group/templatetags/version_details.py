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
from typing import List, Dict
from django import template

from program_management.ddd.domain.service.identity_search import ProgramTreeIdentitySearch
from program_management.ddd.business_types import *

register = template.Library()


@register.simple_tag
def version_details(entity_id: 'NodeIdentity', tree_versions: List['ProgramTreeVersion']) -> Dict[str, str]:
    program_tree_identity = ProgramTreeIdentitySearch().get_from_node_identity(entity_id)
    for program_tree_version in tree_versions:
        if program_tree_version.program_tree_identity == program_tree_identity:
            return {"title": " [{}]".format(program_tree_version.title_fr)if program_tree_version.title_fr else None,
                    "version_label": program_tree_version.version_label}
    return None

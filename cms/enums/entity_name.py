##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.models.enums.education_group_types import GroupType
from program_management.ddd.domain.node import Node

LEARNING_UNIT_YEAR = "learning_unit_year"
OFFER_YEAR = "offer_year"
GROUP_YEAR = "group_year"

ENTITY_NAME = (
    (LEARNING_UNIT_YEAR, LEARNING_UNIT_YEAR),
    (OFFER_YEAR, OFFER_YEAR),
    (GROUP_YEAR, GROUP_YEAR)
)


def get_offers_or_groups_entity_from_node(node: Node):
    return GROUP_YEAR if node.node_type.name in GroupType.get_names() else OFFER_YEAR

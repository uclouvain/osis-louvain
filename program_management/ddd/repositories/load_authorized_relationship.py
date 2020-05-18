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
from base.models.authorized_relationship import AuthorizedRelationship as ModelRelationship, \
    AuthorizedRelationshipObject, AuthorizedRelationshipList
from base.models.education_group_type import EducationGroupType
from program_management.ddd.repositories.load_node import convert_node_type_enum
from program_management.models.enums.node_type import NodeType


def load() -> AuthorizedRelationshipList:  # TODO :: add unit tests
    authorized_relationships = []
    qs = ModelRelationship.objects.all().values(
        'parent_type__name',
        'child_type__name',
        'min_count_authorized',
        'max_count_authorized',
    )
    parent_types_with_authorized_learn_unit = set(
        EducationGroupType.objects.filter(learning_unit_child_allowed=True).values_list('name', flat=True)
    )
    for obj in qs:
        parent_type_name = obj['parent_type__name']
        authorized_relationships.append(
            AuthorizedRelationshipObject(
                convert_node_type_enum(parent_type_name),
                convert_node_type_enum(obj['child_type__name']),
                obj['min_count_authorized'],
                obj['max_count_authorized'],
            )
        )
    for parent_type_name in parent_types_with_authorized_learn_unit:
        authorized_relationships.append(
            AuthorizedRelationshipObject(
                convert_node_type_enum(parent_type_name),
                NodeType.LEARNING_UNIT,
                0,
                999,
            )
        )
    if authorized_relationships:
        return AuthorizedRelationshipList(authorized_relationships)

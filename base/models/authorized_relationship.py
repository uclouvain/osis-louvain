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
import sys
from typing import List, Set, Union

import attr
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models.education_group_type import EducationGroupType
from base.models.enums.education_group_types import EducationGroupTypesEnum, GroupType
from base.utils.constants import INFINITE_VALUE
from osis_common.models.osis_model_admin import OsisModelAdmin
from program_management.models.enums.node_type import NodeType


class AuthorizedRelationshipAdmin(OsisModelAdmin):
    list_display = ('parent_type', 'child_type', 'min_count_authorized', 'max_count_authorized', 'changed')
    search_fields = ['parent_type__name', 'child_type__name']


class AuthorizedRelationship(models.Model):
    parent_type = models.ForeignKey(EducationGroupType, related_name='authorized_parent_type', on_delete=models.CASCADE)
    child_type = models.ForeignKey(EducationGroupType, related_name='authorized_child_type', on_delete=models.CASCADE)
    changed = models.DateTimeField(auto_now=True)

    min_count_authorized = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Minimum number of permitted relationships")
    )
    max_count_authorized = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Maximum number of permitted relationships"),
        help_text=_("A null value means many relationships.")
    )

    def __str__(self):
        return '{} - {}'.format(self.parent_type, self.child_type)


@attr.s(slots=True, frozen=True)
class AuthorizedRelationshipObject:
    parent_type = attr.ib(type=EducationGroupTypesEnum)
    child_type = attr.ib(type=Union[EducationGroupTypesEnum, NodeType])
    min_count_authorized = attr.ib(type=int)
    max_count_authorized = attr.ib(type=int, converter=lambda value: INFINITE_VALUE if value is None else value)


@attr.s()
class AuthorizedRelationshipList:
    authorized_relationships = attr.ib(type=List[AuthorizedRelationshipObject])

    def get_authorized_relationship(
            self,
            parent_type: EducationGroupTypesEnum,
            child_type: Union[EducationGroupTypesEnum, NodeType]
    ) -> AuthorizedRelationshipObject:
        return next(
            (
                auth_rel for auth_rel in self.authorized_relationships
                if auth_rel.child_type == child_type
                and auth_rel.parent_type == parent_type
            ),
            None
        )

    def is_authorized(
            self,
            parent_type: EducationGroupTypesEnum,
            child_type: Union[EducationGroupTypesEnum, NodeType]
    ) -> bool:
        return child_type in self.get_authorized_children_types(parent_type)

    def get_authorized_children_types(
            self,
            parent_type: EducationGroupTypesEnum
    ) -> Set[Union[EducationGroupTypesEnum, NodeType]]:
        return set(
            auth_rel.child_type for auth_rel in self.authorized_relationships
            if auth_rel.parent_type == parent_type
        )

    def get_ordered_mandatory_children_types(
            self,
            parent_type: EducationGroupTypesEnum
    ) -> List[EducationGroupTypesEnum]:
        ordered_group_types = {group_type: order for order, group_type in enumerate(GroupType.ordered())}
        mandatory_children_types = self._get_mandatory_children_types(parent_type)
        types_with_order_value = [
            (child_type, ordered_group_types.get(child_type.name, 999))
            for child_type in mandatory_children_types
        ]
        return [child_type for child_type, order in sorted(types_with_order_value, key=lambda tuple: tuple[1])]

    def is_mandatory_child(self, parent_type: 'EducationGroupTypesEnum', child_type: 'EducationGroupType') -> bool:
        return child_type in self.get_ordered_mandatory_children_types(parent_type)

    def _get_mandatory_children_types(
            self,
            parent_type: EducationGroupTypesEnum
    ) -> Set[EducationGroupTypesEnum]:
        return set(
            authorized_type.child_type
            for authorized_type in self.authorized_relationships
            if isinstance(authorized_type.child_type, EducationGroupTypesEnum)
            and authorized_type.parent_type == parent_type
            and authorized_type.min_count_authorized > 0
        )

    def update(
            self,
            parent_type: EducationGroupTypesEnum,
            child_type: Union[EducationGroupTypesEnum, NodeType],
            min_count_authorized: int = 0,
            max_count_authorized: int = INFINITE_VALUE):
        current_relationship_object = self.get_authorized_relationship(parent_type, child_type)
        self.authorized_relationships.remove(current_relationship_object)

        self.authorized_relationships.append(
            AuthorizedRelationshipObject(
                parent_type=parent_type,
                child_type=child_type,
                min_count_authorized=min_count_authorized,
                max_count_authorized=max_count_authorized)
        )

    def __copy__(self) -> 'AuthorizedRelationshipList':
        return self.__class__(authorized_relationships=self.authorized_relationships.copy())

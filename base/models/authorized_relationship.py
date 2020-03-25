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
from typing import List, Set

from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models.education_group_type import EducationGroupType
from base.models.enums.education_group_types import EducationGroupTypesEnum
from osis_common.models.osis_model_admin import OsisModelAdmin


class AuthorizedRelationshipAdmin(OsisModelAdmin):
    list_display = ('parent_type', 'child_type', 'changed')
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


class AuthorizedRelationshipObject:
    # Object used for typing 'parent_type' and 'child_type' as Enum
    def __init__(
            self,
            parent_type: EducationGroupTypesEnum,
            child_type: EducationGroupTypesEnum,
            min_constraint: int,
            max_constraint: int
    ):
        self.parent_type = parent_type
        self.child_type = child_type
        self.min_count_authorized = min_constraint
        self.max_count_authorized = max_constraint


class AuthorizedRelationshipList:

    def __init__(self, authorized_relationships: List[AuthorizedRelationshipObject]):
        assert authorized_relationships, "You must set at least 1 authorized relation (list can't be empty)"
        assert isinstance(authorized_relationships, list)
        assert isinstance(authorized_relationships[0], AuthorizedRelationshipObject)
        self.authorized_relationships = authorized_relationships

    def get_authorized_relationship(
            self,
            parent_type: EducationGroupTypesEnum,
            child_type: EducationGroupTypesEnum
    ) -> AuthorizedRelationshipObject:
        return next(
            (
                auth_rel for auth_rel in self.authorized_relationships
                if auth_rel.child_type == child_type
                and auth_rel.parent_type == parent_type
            ),
            None
        )

    def is_authorized(self, parent_type: EducationGroupTypesEnum, child_type: EducationGroupTypesEnum) -> bool:
        return child_type in self.get_authorized_children_types(parent_type)

    def get_authorized_children_types(self, parent_type: EducationGroupTypesEnum) -> Set[EducationGroupTypesEnum]:
        return set(
            auth_rel.child_type for auth_rel in self.authorized_relationships
            if auth_rel.parent_type == parent_type
        )

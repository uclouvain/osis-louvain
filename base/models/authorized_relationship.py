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
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models.education_group_type import EducationGroupType
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

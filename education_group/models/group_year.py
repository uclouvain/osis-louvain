##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from education_group.models.enums.constraint_type import ConstraintTypes
from osis_common.models.osis_model_admin import OsisModelAdmin


class GroupYearAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('acronym', 'partial_acronym', 'title_fr', 'group', 'education_group_type', 'changed')
    list_filter = ('education_group_type', )
    search_fields = ['acronym', 'partial_acronym', 'title_fr', 'group__pk', 'id']


class GroupYear(models.Model):

    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    partial_acronym = models.CharField(
        max_length=15,
        db_index=True,
        null=True,
        verbose_name=_("Acronym/Short title"),
    )
    acronym = models.CharField(
        max_length=40,
        db_index=True,
        verbose_name=_("code"),
    )
    education_group_type = models.ForeignKey(
        'base.EducationGroupType',
        verbose_name=_("Type of training"),
        on_delete=models.CASCADE,
        db_index=True
    )
    credits = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("credits"),
    )
    constraint_type = models.CharField(
        max_length=20,
        choices=ConstraintTypes.choices(),
        default=None,
        blank=True,
        null=True,
        verbose_name=_("type of constraint")
    )
    min_constraint = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("minimum constraint"),
        validators=[MinValueValidator(1)]
    )
    max_constraint = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("maximum constraint"),
        validators=[MinValueValidator(1)]
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.CASCADE
    )
    title_fr = models.CharField(
        max_length=255,
        verbose_name=_("Title in French")
    )
    title_en = models.CharField(
        max_length=240,
        blank=True,
        default="",
        verbose_name=_("Title in English")
    )
    remark_fr = models.TextField(
        blank=True,
        default="",
        verbose_name=_("remark")
    )
    remark_en = models.TextField(
        blank=True,
        default="",
        verbose_name=_("remark in english")
    )

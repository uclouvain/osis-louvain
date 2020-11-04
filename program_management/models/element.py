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

from collections import Counter

from django.contrib import admin
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from base.models.academic_year import AcademicYear
from base.models.learning_unit_year import LearningUnitYear
from education_group.models.group_year import GroupYear
from learning_unit.models.learning_class_year import LearningClassYear
from osis_common.models.osis_model_admin import OsisModelAdmin
from program_management.models.enums.node_type import NodeType


class AcademicYearListFilter(admin.SimpleListFilter):
    title = _('Academic year')

    parameter_name = 'academic_year_id'

    def lookups(self, request, model_admin):
        academic_year_ids = set(GroupYear.objects.all().values_list('academic_year', flat=True))
        academic_year_ids.update(set(LearningUnitYear.objects.all().values_list('academic_year', flat=True)))
        academic_year_ids.update(set(
            LearningClassYear.objects.all().values_list(
                'learning_component_year__learning_unit_year__academic_year', flat=True)
        )
        )
        academic_years = AcademicYear.objects.filter(id__in=academic_year_ids)
        ac_list = []
        for ac in academic_years:
            ac_list.append((ac.id, str(ac)))
        return ac_list

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(
                Q(group_year__academic_year_id=value) | Q(learning_unit_year__academic_year_id=value) |
                Q(learning_class_year__learning_component_year__learning_unit_year__academic_year_id=value)
            )


class ElementTypeListFilter(admin.SimpleListFilter):
    title = _('Type')

    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return [
            ('group_year', _('Group')),
            ('learning_unit_year', _('Learning unit year')),
            ('learning_class_year', _('Learning class year'))
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'group_year':
            return queryset.exclude(group_year__isnull=True)
        elif value == 'learning_unit_year':
            return queryset.exclude(learning_unit_year__isnull=True)
        elif value == 'learning_class_year':
            return queryset.exclude(learning_class_year__isnull=True)


class ElementManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'group_year',
            'learning_unit_year',
            'learning_class_year'
        )


class ElementAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('group_year', 'learning_unit_year', 'learning_class_year')
    search_fields = (
        'group_year__acronym',
        'group_year__partial_acronym',
        'learning_unit_year__acronym',
        'learning_class_year__acronym'
    )
    list_filter = (AcademicYearListFilter, ElementTypeListFilter)


class Element(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    group_year = models.OneToOneField(
        'education_group.GroupYear',
        blank=True, null=True,
        verbose_name=_('group year'),
        on_delete=models.PROTECT
    )
    learning_unit_year = models.OneToOneField(
        'base.LearningUnitYear',
        blank=True, null=True,
        verbose_name=_('learning unit year'),
        on_delete=models.PROTECT,
    )
    learning_class_year = models.OneToOneField(
        'learning_unit.LearningClassYear',
        blank=True, null=True,
        verbose_name=_('learning class year'),
        on_delete=models.PROTECT,
    )

    objects = ElementManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(group_year__isnull=False) & Q(learning_unit_year__isnull=True) &
                    Q(learning_class_year__isnull=True)
                ) | (
                    Q(group_year__isnull=True) & Q(learning_unit_year__isnull=False) &
                    Q(learning_class_year__isnull=True)
                ) | (
                    Q(group_year__isnull=True) & Q(learning_unit_year__isnull=True) &
                    Q(learning_class_year__isnull=False)
                ),
                name='only_one_fk_element'
            )
        ]

    def __str__(self):
        field = {
            NodeType.GROUP: self.group_year,
            NodeType.LEARNING_UNIT: self.learning_unit_year,
            NodeType.LEARNING_CLASS: self.learning_class_year,
        }[self.node_type]
        return str(field)

    @property
    def node_type(self):
        if self.group_year:
            return NodeType.GROUP
        elif self.learning_unit_year:
            return NodeType.LEARNING_UNIT
        elif self.learning_class_year:
            return NodeType.LEARNING_CLASS

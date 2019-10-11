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
from django.contrib import admin
from django.db import models


class AttributionChargeNewAdmin(admin.ModelAdmin):
    list_display = ('attribution', 'learning_component_year', 'allocation_charge')
    raw_id_fields = ('attribution', 'learning_component_year')
    search_fields = ['attribution__tutor__person__first_name', 'attribution__tutor__person__last_name',
                     'attribution__tutor__person__global_id',
                     'learning_component_year__learning_unit_year__acronym',
                     'attribution__function']
    list_filter = ('learning_component_year__type', 'attribution__learning_container_year__academic_year')


class AttributionChargeNew(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    attribution = models.ForeignKey('AttributionNew', on_delete=models.CASCADE)
    learning_component_year = models.ForeignKey('base.LearningComponentYear', on_delete=models.CASCADE)
    allocation_charge = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)

    def __str__(self):
        return u"%s" % self.attribution


def search(*args, **kwargs):
    qs = AttributionChargeNew.objects.all()

    if "attribution" in kwargs:
        qs = qs.filter(attribution=kwargs['attribution'])
    if "learning_component_year" in kwargs:
        if isinstance(kwargs['learning_component_year'], list):
            qs = qs.filter(learning_component_year__in=kwargs['learning_component_year'])
        else:
            qs = qs.filter(learning_component_year=kwargs['learning_component_year'])

    return qs.select_related('learning_component_year', 'attribution')

##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from reversion.admin import VersionAdmin

from base.models.enums import component_type
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class LearningUnitComponentAdmin(VersionAdmin, SerializableModelAdmin):
    list_display = ('learning_unit_year', 'learning_component_year', 'type')
    search_fields = ['learning_unit_year__acronym']
    list_filter = ('learning_unit_year__academic_year',)


class LearningUnitComponent(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    learning_unit_year = models.ForeignKey('LearningUnitYear')
    learning_component_year = models.ForeignKey('LearningComponentYear')
    # FIXME :  Duplicate with learningComponentYear.type (check if used in OSIS-portal)
    type = models.CharField(max_length=25, blank=True, null=True, choices=component_type.COMPONENT_TYPES, db_index=True)

    def __str__(self):
        return u"%s - %s" % (self.learning_component_year.type, self.learning_unit_year)


def find_by_learning_year_type(a_learning_unit_year=None, a_type=None):
    if a_learning_unit_year and a_type:
        try:
            return LearningUnitComponent.objects.get(learning_unit_year=a_learning_unit_year,
                                                     type=a_type)
        except ObjectDoesNotExist:
            return None
    return None


def find_by_learning_unit_year(a_learning_unit_year):
    return LearningUnitComponent.objects.filter(learning_unit_year=a_learning_unit_year)\
        .order_by('learning_component_year__acronym')


def find_by_learning_component_year(a_learning_component_year):
    return LearningUnitComponent.objects.filter(learning_component_year=a_learning_component_year)\
        .order_by('learning_unit_year__acronym')


def search(a_learning_component_year=None, a_learning_unit_year=None):
    queryset = LearningUnitComponent.objects
    if a_learning_component_year:
        queryset = queryset.filter(learning_component_year=a_learning_component_year)

    if a_learning_unit_year:
        queryset = queryset.filter(learning_unit_year=a_learning_unit_year)

    return queryset.select_related('learning_unit_year__academic_year')


def used_by(learning_component_year, learning_unit_year):
    if search(learning_component_year, learning_unit_year).exists():
        return True
    return False

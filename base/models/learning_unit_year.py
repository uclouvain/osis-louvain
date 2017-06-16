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
from django.db import models
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin
from base.models.enums import learning_unit_year_activity_status, learning_unit_year_subtypes


class LearningUnitYearAdmin(SerializableModelAdmin):
    list_display = ('acronym', 'title', 'academic_year', 'credits', 'changed', 'structure')
    fieldsets = ((None, {'fields': ('academic_year', 'learning_unit', 'acronym', 'title', 'title_english', 'credits',
                                    'decimal_scores', 'structure', 'learning_container_year', 'activity_status')}),)
    list_filter = ('academic_year', 'vacant', 'in_charge', 'decimal_scores')
    raw_id_fields = ('learning_unit', 'learning_container_year', 'structure')
    search_fields = ['acronym', 'structure__acronym']


class LearningUnitYear(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    academic_year = models.ForeignKey('AcademicYear')
    learning_unit = models.ForeignKey('LearningUnit')
    learning_container_year = models.ForeignKey('LearningContainerYear', blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    acronym = models.CharField(max_length=15, db_index=True)
    title = models.CharField(max_length=255)
    title_english = models.CharField(max_length=250, blank=True, null=True)
    subtype = models.CharField(max_length=50, blank=True, null=True,
                               choices=learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES)
    credits = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    decimal_scores = models.BooleanField(default=False)
    team = models.BooleanField(default=False)
    vacant = models.BooleanField(default=False)
    in_charge = models.BooleanField(default=False)
    structure = models.ForeignKey('Structure', blank=True, null=True)
    activity_status = models.CharField(max_length=20, blank=True, null=True,
                                       choices=learning_unit_year_activity_status.LEARNING_UNIT_YEAR_ACTIVITY_STATUS)

    def __str__(self):
        return u"%s - %s" % (self.academic_year, self.acronym)

    @property
    def subdivision(self):
        if self.acronym and self.learning_container_year:
            return self.acronym.replace(self.learning_container_year.acronym, "")
        return None

def find_by_id(learning_unit_year_id):
    return LearningUnitYear.objects.get(pk=learning_unit_year_id)


def find_by_acronym(acronym):
    return LearningUnitYear.objects.filter(acronym=acronym)\
                                   .select_related('learning_container_year')


def search(academic_year_id=None, acronym=None, learning_container_year_id=None, learning_unit=None,
           title=None, subtype=None, activity_status=None):
    queryset = LearningUnitYear.objects

    if academic_year_id:
        queryset = queryset.filter(academic_year=academic_year_id)

    if acronym:
        queryset = queryset.filter(acronym__icontains=acronym)

    if learning_container_year_id:
        queryset = queryset.filter(learning_container_year=learning_container_year_id)

    if learning_unit:
        queryset = queryset.filter(learning_unit=learning_unit)

    if title:
        queryset = queryset.filter(title__icontains=title)

    if subtype:
        queryset = queryset.filter(subtype=subtype)

    if activity_status:
        queryset = queryset.filter(activity_status=activity_status)

    return queryset.select_related('learning_container_year')

##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import admin


class AttributionAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'function', 'learning_unit_year', 'start_date', 'end_date', 'changed')
    list_filter = ('function',)
    fieldsets = ((None, {'fields': ('learning_unit_year', 'tutor', 'function', 'start_date', 'end_date')}),)
    raw_id_fields = ('learning_unit_year', 'tutor')
    search_fields = ['tutor__person__first_name', 'tutor__person__last_name', 'learning_unit_year__acronym']


class Attribution(models.Model):
    FUNCTION_CHOICES = (
        ('COORDINATOR', 'Coordinator'),
        ('PROFESSOR', 'Professor'))

    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    start_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    end_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    function = models.CharField(max_length=15, blank=True, null=True, choices=FUNCTION_CHOICES, db_index=True)
    learning_unit_year = models.ForeignKey('LearningUnitYear', blank=True, null=True, default=None)
    learning_unit = models.ForeignKey('LearningUnit', blank=True, null=True, default=None)  # To remove, not present in
    tutor = models.ForeignKey('Tutor')                                                      # db

    def __str__(self):
        return u"%s - %s" % (self.tutor.person, self.function)


def search(tutor=None, learning_unit_year=None, function=None, list_learning_unit_year=None):
    queryset = Attribution.objects

    if tutor:
        queryset = queryset.filter(tutor=tutor)

    if learning_unit_year:
        queryset = queryset.filter(learning_unit_year=learning_unit_year)

    if function:
        queryset = queryset.filter(function=function)

    if list_learning_unit_year:
        queryset = queryset.filter(learning_unit_year__in=list_learning_unit_year)

    return queryset.select_related('tutor', 'learning_unit_year')


def find_responsible(a_learning_unit_year):
    # If there are more than 1 coordinator, we take the first in alphabetic order
    attribution_list = Attribution.objects.filter(learning_unit_year=a_learning_unit_year)\
                                                      .filter(function='COORDINATOR')

    if attribution_list and len(attribution_list) > 0:
        if len(attribution_list) == 1:
            return attribution_list[0].tutor
        else:
            for lu_attribution in attribution_list:
                if lu_attribution.function == 'COORDINATOR':
                    return lu_attribution.tutor
            return attribution_list[0].tutor
    return None


def is_coordinator(user, learning_unit_year):
    """
    :param user:
    :param learning_unit_year:
    :return: True is the user is coordinator for the learningUnit passed in parameter.
    """
    attributions = Attribution.objects.filter(learning_unit_year=learning_unit_year)\
                                      .filter(function='COORDINATOR')\
                                      .filter(tutor__person__user=user)\
                                      .count()
    return attributions > 0
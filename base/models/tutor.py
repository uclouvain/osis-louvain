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
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib import admin
from base.models import person, attribution, session_exam


class TutorAdmin(admin.ModelAdmin):
    list_display = ('person', 'changed')
    fieldsets = ((None, {'fields': ('person',)}),)
    raw_id_fields = ('person', )
    search_fields = ['person__first_name', 'person__last_name']


class Tutor(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    person = models.OneToOneField('Person')

    def __str__(self):
        return u"%s" % self.person


def find_by_user(user):
    try:
        pers = person.find_by_user(user)
        tutor = Tutor.objects.get(person=pers)
        return tutor
    except ObjectDoesNotExist:
        return None


def find_by_person(a_person):
    try:
        tutor = Tutor.objects.get(person=a_person)
        return tutor
    except ObjectDoesNotExist:
        return None


def find_by_id(tutor_id):
    return Tutor.objects.get(id=tutor_id)


def find_responsible(a_learning_unit):
    # If there are more than 1 coordinator, we take the first in alphabetic order
    attribution_list = attribution.Attribution.objects.filter(learning_unit=a_learning_unit)\
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


def is_coordinator(user, learning_unit_id):
    """
    :param user:
    :param learning_unit_id:
    :return: True is the user is coordinator for the learningUnit passed in parameter.
    """
    attributions = attribution.Attribution.objects.filter(learning_unit_id=learning_unit_id)\
                                      .filter(function='COORDINATOR')\
                                      .filter(tutor__person__user=user)\
                                      .count()
    return attributions > 0


def find_by_learning_unit(learning_unit_id):
    """
    :param learning_unit_id:
    :return: All tutors of the learningUnit passed in parameter.
    """
    tutor_ids = attribution.search(learning_unit_id=learning_unit_id).values_list('tutor', flat=True).distinct('tutor')
    return Tutor.objects.filter(pk__in=tutor_ids).order_by('person__last_name', 'person__first_name')

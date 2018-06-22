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
from django.db import models
from django.contrib import messages
from django.contrib.auth.models import Group
from django.db.models import Q

from attribution.models import attribution
from base.models import person
from osis_common.models import serializable_model


class TutorAdmin(serializable_model.SerializableModelAdmin):
    actions = ['add_to_group']
    list_display = ('person', 'changed')
    list_filter = ('person__gender', 'person__language')
    search_fields = ['person__first_name', 'person__last_name', 'person__global_id']

    def add_to_group(self, request, queryset):
        group_name = "tutors"
        try:
            group = Group.objects.get(name=group_name)
            count = 0
            for tutor in queryset:
                user = tutor.person.user
                if user and not user.groups.filter(name=group_name).exists():
                    user.groups.add(group)
                    count += 1
            self.message_user(request, "{} users added to the group 'tutors'.".format(count), level=messages.SUCCESS)
        except Group.DoesNotExist:
            self.message_user(request, "Group {} doesn't exist.".format(group_name), level=messages.ERROR)


class Tutor(serializable_model.SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    person = models.OneToOneField('Person')

    def __str__(self):
        return u"%s" % self.person


def find_by_user(user):
    try:
        pers = person.find_by_user(user)
        return Tutor.objects.get(person=pers)
    except Tutor.DoesNotExist:
        return None


def find_by_person(a_person):
    try:
        return Tutor.objects.get(person=a_person)
    except Tutor.DoesNotExist:
        return None


def find_by_id(tutor_id):
    try:
        return Tutor.objects.get(id=tutor_id)
    except Tutor.DoesNotExist:
        return None


# To refactor because it is not in the right place.
def find_by_learning_unit(learning_unit_year):
    """
    :param learning_unit_year:
    :return: All tutors of the learningUnit passed in parameter.
    """
    if isinstance(learning_unit_year, list):
        queryset = attribution.search(list_learning_unit_year=learning_unit_year)
    else:
        queryset = attribution.search(learning_unit_year=learning_unit_year)
    tutor_ids = queryset.values_list('tutor').distinct('tutor')
    return Tutor.objects.filter(pk__in=tutor_ids)\
                        .select_related('person')\
                        .order_by('person__last_name', 'person__first_name')


def is_tutor(user):
    """
    :param user:
    :return: True if the user is a tutor. False if the user is not a tutor.
    """
    return Tutor.objects.filter(person__user=user).count() > 0


def search(**criterias):
    queryset = Tutor.objects.all()
    if "name" in criterias:
        full_name = criterias["name"]
        for name in full_name.split():
            queryset = queryset.filter(Q(person__first_name__icontains=name) | Q(person__last_name__icontains=name))
    return queryset.distinct().select_related("person")


def find_all_summary_responsibles_by_learning_unit_year(a_learning_unit_year):
    return Tutor.objects.filter(attribution__learning_unit_year=a_learning_unit_year,
                                attribution__summary_responsible=True)

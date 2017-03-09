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
from django.core.exceptions import ObjectDoesNotExist
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin
from base import signals

class StudentAdmin(SerializableModelAdmin):
    list_display = ('person', 'registration_id', 'changed')
    fieldsets = ((None, {'fields': ('registration_id', 'person')}),)
    raw_id_fields = ('person', )
    search_fields = ['person__first_name', 'person__last_name', 'registration_id']


class Student(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    registration_id = models.CharField(max_length=10, unique=True)
    person = models.ForeignKey('Person')

    def __str__(self):
        return u"%s (%s)" % (self.person, self.registration_id)

    def delete(self, *args, **kwargs):
        super(Student, self).delete(*args, **kwargs)
        if self.person.user:
            signals.remove_user_from_group.send(sender=self.__class__, instance=self.person.user, group="students")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super(Student, self).save(*args, **kwargs)
        if is_new and self.person.user:
            signals.add_user_to_group.send(sender=self.__class__, instance=self.person.user, group="students")



def find_by(registration_id=None, person_name=None, person_username=None, person_first_name=None, full_registration = None):
    """
    Find students by optional arguments. At least one argument should be informed
    otherwise it returns empty.
    """
    out = None
    queryset = Student.objects

    if registration_id:
        if (full_registration):
            queryset = queryset.filter(registration_id=registration_id)
        else :
            queryset = queryset.filter(registration_id__icontains=registration_id)

    if person_name:
        queryset = queryset.filter(person__last_name__icontains=person_name)

    if person_username:
        queryset = queryset.filter(person__user=person_username)

    if person_first_name:
        queryset = queryset.filter(person__first_name__icontains=person_first_name)

    if registration_id or person_name or person_username or person_first_name:
        out = queryset

    return out


def find_by_registration_id(registration_id):
    try:
        return Student.objects.get(registration_id=registration_id)
    except ObjectDoesNotExist:
        return None


def find_by_person(a_person):
    try:
        student = Student.objects.get(person=a_person)
        return student
    except ObjectDoesNotExist:
        return None


def find_by_offer(offers):
    return Student.objects.filter(offerenrollment__offer_year__offer__in=offers)


def find_by_offer_year(offer_y):
    return Student.objects.filter(offerenrollment__offer_year=offer_y)


def find_by_id(student_id):
    try:
        return Student.objects.get(pk=student_id)
    except ObjectDoesNotExist:
        return None

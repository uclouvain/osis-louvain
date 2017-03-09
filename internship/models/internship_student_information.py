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
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin
from django.utils.translation import ugettext_lazy as _
from base import signals


class InternshipStudentInformationAdmin(SerializableModelAdmin):
    list_display = ('person', 'location', 'postal_code', 'city', 'country', 'latitude', 'longitude', 'email',
                    'phone_mobile', 'contest')
    fieldsets = ((None, {'fields': ('person', 'location', 'postal_code', 'city', 'latitude', 'longitude', 'country',
                                    'email', 'phone_mobile', 'contest')}),)
    raw_id_fields = ('person',)
    search_fields = ['person__user__username', 'person__last_name', 'person__first_name']


class InternshipStudentInformation(SerializableModel):
    TYPE_CHOICE = (('SPECIALIST', _('specialist')),
                   ('GENERALIST', _('generalist')))
    person = models.ForeignKey('base.Person')
    location = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone_mobile = models.CharField(max_length=100, blank=True, null=True)
    contest = models.CharField(max_length=124, choices=TYPE_CHOICE, default="GENERALIST")

    def __str__(self):
        return '{}'.format(self.person)

    def delete(self, *args, **kwargs):
        super(InternshipStudentInformation, self).delete(*args, **kwargs)
        if self.person.user:
            signals.remove_user_from_group.send(sender=self.__class__, instance=self.person.user, group="internship_students")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super(InternshipStudentInformation, self).save(*args, **kwargs)
        if is_new and self.person.user:
            signals.add_user_to_group.send(sender=self.__class__, instance=self.person.user, group="internship_students")


def search(**kwargs):
    kwargs = {k: v for k, v in kwargs.items() if v}
    queryset = InternshipStudentInformation.objects.filter(**kwargs).select_related("person")
    return queryset


def find_all():
    return InternshipStudentInformation.objects.all()\
        .select_related("person")\
        .order_by('person__last_name', 'person__first_name')


def find_by_person(person):
    try:
        return InternshipStudentInformation.objects.get(person=person)
    except ObjectDoesNotExist:
        return None


def get_number_of_specialists():
    contest_specialist = "SPECIALIST"
    return InternshipStudentInformation.objects.filter(contest=contest_specialist).count()


def get_number_of_generalists():
    contest_generalist = "GENERALIST"
    return InternshipStudentInformation.objects.filter(contest=contest_generalist).count()


def get_number_students():
    return InternshipStudentInformation.objects.count()

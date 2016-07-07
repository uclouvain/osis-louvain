##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin


class AdviserAdmin(admin.ModelAdmin):
    list_display = ('person', 'type')


class Adviser(models.Model):
    TYPES_CHOICES = (
        ('PRF', _('Professor')),
        ('MGR', _('Manager')),
    )

    person = models.OneToOneField('base.Person', on_delete=models.CASCADE)
    type = models.CharField(max_length=3, choices=TYPES_CHOICES, default='PRF')
    available_by_email = models.BooleanField(default=False)
    available_by_phone = models.BooleanField(default=False)
    available_at_office = models.BooleanField(default=False)
    comment = models.TextField(default='', blank=True)

    def __str__(self):
        first_name = ""
        middle_name = ""
        last_name = ""
        if self.person.first_name:
            first_name = self.person.first_name
        if self.person.middle_name:
            middle_name = self.person.middle_name
        if self.person.last_name:
            last_name = self.person.last_name + ","
        return u"%s %s %s" % (last_name.upper(), first_name, middle_name)

    class Meta:
        ordering = ["person__last_name", "person__middle_name", "person__first_name"]


def find_by_person(a_person):
    adviser = Adviser.objects.get(person=a_person)
    return adviser


def search_adviser(terms):
    queryset = Adviser.objects.all().filter(type='PRF')
    if terms:
        queryset = queryset.filter(
            (Q(person__first_name__icontains=terms) | Q(person__last_name__icontains=terms)) &
            Q(type='PRF')).distinct()
    return queryset

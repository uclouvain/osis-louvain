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
from base.models import person
from django.core.exceptions import ObjectDoesNotExist


class ProgramManagerAdmin(admin.ModelAdmin):
    list_display = ('person', 'offer_year')
    raw_id_fields = ('person', 'offer_year')
    search_fields = ['person__first_name', 'person__last_name', 'offer_year__acronym']


class ProgramManager(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    person = models.ForeignKey('Person')
    offer_year = models.ForeignKey('OfferYear')

    @property
    def name(self):
        return self.__str__()

    def __str__(self):
        return u"%s - %s" % (self.person, self.offer_year)


def find_by_person(a_person):
    programs_managed = ProgramManager.objects.filter(person=a_person)
    return programs_managed


def is_programme_manager(user, offer_yr):
    try:
        pers = person.Person.objects.get(user=user)
        if user:
            programme_manager = ProgramManager.objects.filter(person=pers.id, offer_year=offer_yr)
            if programme_manager:
                return True
    except ObjectDoesNotExist:
        return False


def find_by_offer_year(offer_yr):
    return ProgramManager.objects.filter(offer_year=offer_yr)


def find_by_user(user):
    return ProgramManager.objects.filter(person__user=user)\
                                 .order_by('offer_year__acronym')

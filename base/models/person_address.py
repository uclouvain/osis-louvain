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


class PersonAddressAdmin(admin.ModelAdmin):
    list_display = ('person', 'label', 'location', 'postal_code', 'city', 'country')
    fieldsets = ((None, {'fields': ('person', 'label', 'location', 'postal_code', 'city', 'country')}),)


class PersonAddress(models.Model):
    person      = models.ForeignKey('Person')
    label       = models.CharField(max_length=20)
    location    = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city        = models.CharField(max_length=255)
    country     = models.CharField(max_length=255)


def find_by_person(a_person):
    """ Return a list containing one or more addresses of a person. Returns None if there is no address.
    :param a_person: An instance of the class base.models.person.Person
    """
    return PersonAddress.objects.filter(person=a_person)

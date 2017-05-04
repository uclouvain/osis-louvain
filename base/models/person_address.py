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
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin


LABELS = (
    ('RESIDENTIAL', _('residential')),
    ('PROFESSIONAL', _('professional'))
)


class PersonAddressAdmin(admin.ModelAdmin):
    list_display = ('person', 'label', 'location', 'postal_code', 'city', 'country')
    search_fields = ['person__first_name', 'person__last_name', 'person__global_id']
    fieldsets = ((None, {'fields': ('person', 'label', 'location', 'postal_code', 'city', 'country')}),)
    raw_id_fields = ('person',)
    list_filter = ('label', 'city')


class PersonAddress(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    person = models.ForeignKey('Person')
    label = models.CharField(max_length=20, choices=LABELS)
    location = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=255)
    country = models.ForeignKey('reference.Country')


def find_by_person(a_person):
    """ Return a list containing one or more addresses of a person. Returns None if there is no address.
    :param a_person: An instance of the class base.models.person.Person
    """
    return PersonAddress.objects.filter(person=a_person)


def find_by_person_label(a_person, a_label):
    """ Return a list containing one address of a person. Returns the first one if there are several addresses.
    :param a_person: An instance of the class base.models.person.Person
    :param a_label:  A specific label to look for
    """
    return PersonAddress.objects.filter(person=a_person).filter(label=a_label).first()

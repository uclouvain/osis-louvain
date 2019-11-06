##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.models.enums.person_address_type import PersonAddressType
from osis_common.models.osis_model_admin import OsisModelAdmin


class PersonAddressAdmin(OsisModelAdmin):
    list_display = ('person', 'label', 'location', 'postal_code', 'city', 'country')
    search_fields = ['person__first_name', 'person__last_name', 'person__global_id']
    raw_id_fields = ('person',)
    list_filter = ('label', 'city')


class PersonAddress(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    location = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.ForeignKey('reference.Country', blank=True, null=True, on_delete=models.PROTECT)
    label = models.CharField(max_length=20, choices=PersonAddressType.choices(),
                             default=PersonAddressType.PROFESSIONAL.value)


def find_by_person(a_person):
    return PersonAddress.objects.filter(person=a_person)


def get_by_label(a_person, a_label):
    return PersonAddress.objects.filter(person=a_person).filter(label=a_label).first()

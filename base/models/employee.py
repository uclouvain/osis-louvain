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
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class EmployeeAdmin(SerializableModelAdmin):
    list_display = ('person', )
    fieldsets = ((None, {'fields': ('person',)}),)
    search_fields = ['person__first_name', 'person__last_name', 'person__global_id']
    raw_id_fields = ('person',)


class Employee(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    person = models.OneToOneField('Person')


    def __str__(self):
        return u"%s" % self.person


def search(a_lastname_part, a_first_name_part):
    out = None
    queryset = Employee.objects

    if a_lastname_part:
        queryset = queryset.filter(person__last_name__icontains=a_lastname_part)

    if a_first_name_part:
        queryset = queryset.filter(person__first_name__icontains=a_first_name_part)

    if a_lastname_part or a_first_name_part :
        out = queryset.select_related('person').order_by('person__last_name', 'person__first_name')

    return out


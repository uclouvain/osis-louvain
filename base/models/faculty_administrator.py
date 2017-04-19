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
from base.models import person
from base.enums import structure_type


class FacultyAdministratorAdmin(SerializableModelAdmin):
    list_display = ('employee', 'structure')
    fieldsets = ((None, {'fields': ('employee', 'structure',)}),)
    search_fields = ['employee__person__first_name', 'employee__person__last_name', 'structure__acronym']
    raw_id_fields = ('employee', 'structure')


class FacultyAdministrator(SerializableModel):
    employee = models.ForeignKey('Employee')
    structure = models.ForeignKey('Structure')

    def __str__(self):
        return u"%s" % self.employee

    class Meta:
        permissions = (
            ("is_faculty_administrator", "Is faculty administrator"),
        )


def _get_perms(model):
    return model._meta.permissions


def find_faculty_administrator_by_user(a_user):
    a_person = person.find_by_user(a_user)
    if a_person:
        faculty_administrators = FacultyAdministrator.objects.filter(employee__person=a_person,
                                                                     structure__type=structure_type.FACULTY)
        for f in faculty_administrators:
            return f
    return None


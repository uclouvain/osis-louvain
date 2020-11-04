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

from base.models.enums.organization_type import MAIN
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


LOUVAIN_LA_NEUVE_CAMPUS_NAME = "Louvain-la-Neuve"


class CampusAdmin(SerializableModelAdmin):
    list_display = ('name', 'organization', 'is_administration', 'changed')
    list_filter = ('organization', 'is_administration')
    search_fields = ['name', 'organization__name']


class Campus(SerializableModel):
    name = models.CharField(max_length=100)
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    is_administration = models.BooleanField(default=False)

    def __str__(self):
        return "{} - {}".format(self.name, self.organization)

    class Meta:
        verbose_name_plural = 'campuses'


def find_main_campuses():
    return Campus.objects.filter(organization__type=MAIN).order_by('name').select_related('organization')


def find_by_id(campus_id):
    try:
        return Campus.objects.get(id=campus_id)
    except Campus.DoesNotExist:
        return None


def find_by_name_and_organization_name(name, organization_name):
    try:
        return Campus.objects.get(name=name, organization__name=organization_name)
    except Campus.DoesNotExist:
        return None

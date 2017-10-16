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

from base.models.enums import organization_type
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class OrganizationAdmin(SerializableModelAdmin):
    list_display = ('name', 'acronym', 'prefix', 'type', 'changed')
    fieldsets = ((None, {'fields': ('name', 'acronym', 'prefix', 'website', 'type', 'logo')}),)
    search_fields = ['acronym']


class Organization(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True, null=True)
    acronym = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=30, blank=True, null=True, choices=organization_type.ORGANIZATION_TYPE, default='UNKNOWN')
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    prefix = models.CharField(max_length=30, blank=True, null=True)
    logo = models.ImageField(upload_to='organization_logos', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        permissions = (
            ("can_access_organization", "Can access organization"),
        )


def find_by_id(organization_id):
    return Organization.objects.get(pk=organization_id)


def search(acronym=None, name=None, type=None, prefix=None):
    out  = None
    queryset = Organization.objects

    if acronym:
        queryset = queryset.filter(acronym__iexact=acronym)

    if name:
        queryset = queryset.filter(name__icontains=name)

    if type:
        queryset = queryset.filter(type=type)

    if prefix:
        queryset = queryset.filter(prefix=prefix)

    if acronym or name or type or prefix:
        out = queryset

    return out

def find_by_type(type, order_by=None):

    if order_by:
        queryset = Organization.objects.filter(type=type).order_by(*order_by)
    else:
        queryset = Organization.objects.filter(type=type)

    return queryset

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
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class EntityAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'organization')
    search_fields = ['external_id', 'entityversion__acronym', 'organization__acronym', 'organization__name']
    readonly_fields = ('organization', 'external_id')


class Entity(models.Model):
    organization = models.ForeignKey('Organization', blank=True, null=True)
    external_id = models.CharField(max_length=255, unique=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    location = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "entities"

    def __str__(self):
        return "{0} - {1}".format(self.id, self.external_id)


def search(**kwargs):
    queryset = Entity.objects

    if 'acronym' in kwargs:
        queryset = queryset.filter(entityversion__acronym__icontains=kwargs['acronym'])

    if 'entity_type' in kwargs:
        queryset = queryset.filter(entityversion__entity_type__icontains=kwargs['entity_type'])

    if 'version_date' in kwargs:
        queryset = queryset.filter(entityversion__start_date__lte=kwargs['version_date'],
                                   entityversion__end_date__gte=kwargs['version_date'])

    return queryset


def get_by_internal_id(internal_id):
    try:
        return Entity.objects.get(id__exact=internal_id)
    except ObjectDoesNotExist:
        return None


def get_by_external_id(external_id):
    try:
        return Entity.objects.get(external_id__exact=external_id)
    except ObjectDoesNotExist:
        return None

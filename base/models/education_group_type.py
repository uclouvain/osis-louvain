##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.models.enums import education_group_categories
from osis_common.models.osis_model_admin import OsisModelAdmin


GROUP_TYPE_OPTION = 'Option'


class EducationGroupTypeAdmin(OsisModelAdmin):
    list_display = ('name', 'category', )
    list_filter = ('name', 'category', )
    search_fields = ['name', 'category']


class EducationGroupTypeManager(models.Manager):
    def get_by_natural_key(self, category, name):
        return self.get(category=category, name=name)


class EducationGroupType(models.Model):

    objects = EducationGroupTypeManager()

    external_id = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=25, choices=education_group_categories.CATEGORIES,
                                default=education_group_categories.TRAINING)
    name = models.CharField(max_length=255)

    def __str__(self):
        return u"%s" % self.name

    def natural_key(self):
        return self.category, self.name


def search(**kwargs):
    queryset = EducationGroupType.objects

    if 'category' in kwargs:
        queryset = queryset.filter(category=kwargs['category'])

    return queryset


def find_all():
    return EducationGroupType.objects.order_by('name')


def find_authorized_types(category=None, parent_type=None):
    if category:
        queryset = search(category=category)
    else:
        queryset = EducationGroupType.objects.all()
    if parent_type:
        queryset = queryset.exclude(pk__in=parent_type.unauthorized_parent_type.all().values_list('child_type',
                                                                                                  flat=True))
    return queryset.order_by('name')


def find_by_name(name=None):
    return EducationGroupType.objects.filter(name=name)

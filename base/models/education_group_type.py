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
import collections

from django.db import models
from django.db.models import Case, When
from django.utils.translation import ugettext_lazy as _

from base.models.enums import education_group_categories
from osis_common.models.osis_model_admin import OsisModelAdmin

GROUP_TYPE_OPTION = 'Option'


class EducationGroupTypeAdmin(OsisModelAdmin):
    list_display = ('name', 'category', )
    list_filter = ('name', 'category', )
    search_fields = ['name', 'category']


class EducationGroupTypeQueryset(models.QuerySet):

    def order_by_translated_name(self):
        query_set_dict = self.in_bulk()
        if query_set_dict:
            pk_list = sorted(query_set_dict, key=lambda education_grp_type: _(query_set_dict[education_grp_type].name))
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pk_list)])
            return self.order_by(preserved)
        return self


class EducationGroupTypeManager(models.Manager):
    def get_queryset(self):
        return EducationGroupTypeQueryset(self.model, using=self._db)

    def get_by_natural_key(self, external_id):
        return self.get(external_id=external_id)


class EducationGroupType(models.Model):

    objects = EducationGroupTypeManager()

    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    category = models.CharField(
        max_length=25,
        choices=education_group_categories.CATEGORIES,
        default=education_group_categories.TRAINING,
        verbose_name=_('Category'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('Type of training'),
    )

    def __str__(self):
        return u"%s" % self.name

    def natural_key(self):
        return (self.external_id,)


def search(**kwargs):
    queryset = EducationGroupType.objects

    if 'category' in kwargs:
        queryset = queryset.filter(category=kwargs['category'])

    return queryset


def find_authorized_types(category=None, parents=None):
    if category:
        queryset = search(category=category)
    else:
        queryset = EducationGroupType.objects.all()

    if parents:
        if not isinstance(parents, collections.Iterable):
            parents = [parents]

        # Consecutive filters : we want to match all types not any types
        for parent in parents:
            queryset = queryset.filter(
                authorized_child_type__parent_type__educationgroupyear=parent
            )

    return queryset.order_by_translated_name()


def find_by_name(name=None):
    return EducationGroupType.objects.filter(name=name)

##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Set

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from base.models.entity_version import EntityVersion
from base.models.person import Person
from osis_role.contrib.helper import EntityRoleHelper


class EntityRoleChoiceFieldMixin:
    """
       Mixin which allows to display entities which have a link with person according to all
       EntityRoleModel declared in OSIS Role Manager
    """
    def get_queryset(self):
        entities_link_to_user = EntityRoleHelper.get_all_entities(self.get_person(), self.get_group_names())
        date = timezone.now()
        return EntityVersion.objects.current(date).filter(
            entity__in=entities_link_to_user
        ).select_related('entity__organization')

    def get_person(self) -> Person:
        raise ImproperlyConfigured('You must set a get_person method')

    def get_group_names(self) -> Set[str]:
        raise ImproperlyConfigured('You must set a get_group_names method')


class EntityRoleModelChoiceField(EntityRoleChoiceFieldMixin, forms.ModelChoiceField):
    """
        ModelChoiceField which allow to display entities which have a link with person according to all
        EntityRoleModel declared in OSIS Role Manager
    """
    def __init__(self, person=None, group_names=None, **kwargs):
        self._group_names = group_names
        self._person = person
        if 'queryset' not in kwargs:
            kwargs['queryset'] = self.get_queryset()
        super().__init__(**kwargs)

    def label_from_instance(self, obj):
        return obj.verbose_title

    def clean(self, value):
        entity_version = super().clean(value)
        return entity_version.entity if entity_version else None

    def get_group_names(self) -> Set[str]:
        return self._group_names

    def get_person(self) -> Person:
        return self._person

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
from django import forms
from django.utils import timezone

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from education_group.auth.scope import Scope
from osis_role import role


class EntityRoleChoiceField(forms.ModelChoiceField):
    """
       ModelChoiceField which allow to display entities which have a link with person according to all
       EntityRoleModel declared in OSIS Role Manager
    """
    def __init__(self, person, group_names, **kwargs):
        self._group_names = group_names
        self._person = person
        kwargs['queryset'] = self.get_queryset()
        super().__init__(**kwargs)

    def get_group_names(self):
        return self._group_names

    def get_person(self):
        return self._person

    def get_queryset(self):
        entities_link_to_user = self._get_entities_linked_to_user()
        date = timezone.now()
        return EntityVersion.objects.current(date).filter(
            entity__in=entities_link_to_user
        ).select_related('entity__organization')

    def _get_entities_linked_to_user(self):
        role_mdls = [r for r in role.role_manager.roles if r.group_name in self.get_group_names()]
        qs = None
        for role_mdl in role_mdls:
            subqs = role_mdl.objects.filter(person=self.get_person())
            if hasattr(role_mdl, 'scopes'):
                subqs = subqs.filter(scopes=[Scope.ALL.value])
            subqs = subqs.values('entity_id', 'with_child')
            if qs is None:
                qs = subqs
            else:
                qs = qs.union(subqs)
        return qs.get_entities_ids() if qs else Entity.objects.none()

    def label_from_instance(self, obj):
        return obj.verbose_title

    def clean(self, value):
        entity_version = super().clean(value)
        return entity_version.entity if entity_version else None

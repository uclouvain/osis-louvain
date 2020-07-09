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
import rules
from django.contrib.auth.models import Group, User
from django.core.exceptions import ImproperlyConfigured
from django.db import models

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.person import Person


class RoleQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):
        for obj in self:
            obj.delete()


class RoleModelMeta(models.base.ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        attrs_meta = attrs.get('Meta', None)
        abstract = getattr(attrs_meta, 'abstract', False)
        group_name = getattr(attrs_meta, 'group_name', None)

        if abstract is False:
            if group_name is None:
                raise ImproperlyConfigured('group_name Meta data must be defined in RoleModel subclasses')
            delattr(attrs_meta, 'group_name')
            attrs['Meta'] = attrs_meta

        super_new = super().__new__(cls, name, bases, attrs, **kwargs)
        super_new._meta.group_name = group_name
        setattr(super_new, 'group_name', group_name)
        return super_new


class RoleModel(models.Model, metaclass=RoleModelMeta):
    objects = RoleQuerySet.as_manager()
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._add_user_to_group()
        return self

    def delete(self, *args, **kwargs):
        person = self.person
        super().delete(*args, kwargs)
        self._remove_user_from_group(person)

    @classmethod
    def belong_to(cls, person):
        return cls.objects.filter(person=person).exists()

    @classmethod
    def rule_set(cls):
        return rules.RuleSet({})

    def _add_user_to_group(self):
        try:
            group, _ = Group.objects.get_or_create(name=self.group_name)
            self.person.user.groups.add(group)
        except User.DoesNotExist:
            pass

    def _remove_user_from_group(self, person):
        if not self.belong_to(person):
            group, _ = Group.objects.get_or_create(name=self.group_name)
            person.user.groups.remove(group)


class EntityRoleModelQueryset(models.QuerySet):
    def get_entities_ids(self):
        person_entities = self.values('entity_id', 'with_child')
        entities_with_child = {entity['entity_id'] for entity in person_entities if entity['with_child']}
        entity_version_tree = EntityVersion.objects.get_tree(entities_with_child)
        entities_without_child = {entity['entity_id'] for entity in person_entities if not entity['with_child']}
        return entities_without_child | {node['entity_id'] for node in entity_version_tree}


class EntityRoleModel(RoleModel):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    with_child = models.BooleanField(default=False)

    objects = EntityRoleModelQueryset.as_manager()

    class Meta:
        abstract = True
        unique_together = ('person', 'entity',)

    @classmethod
    def get_person_related_entities(cls, person):
        return cls.objects.filter(person=person).values_list('entity_id', flat=True)

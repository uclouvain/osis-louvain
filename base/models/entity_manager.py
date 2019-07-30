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
from django.db.models import Prefetch
from reversion.admin import VersionAdmin

from base.models import entity_version
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class EntityManagerAdmin(VersionAdmin, SerializableModelAdmin):
    list_display = ('person', 'structure', 'entity')
    search_fields = ['person__first_name', 'person__last_name', 'structure__acronym']


class EntityManager(SerializableModel):
    person = models.ForeignKey('Person', on_delete=models.PROTECT)
    structure = models.ForeignKey('Structure', on_delete=models.CASCADE)
    entity = models.ForeignKey('Entity', blank=True, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return u"%s" % self.person


def get_perms(model):
    return model._meta.permissions


def find_by_user(a_user, with_entity_version=True):
    qs = EntityManager.objects.filter(person__user=a_user)\
                              .select_related('person', 'structure', 'entity')\
                              .order_by('structure__acronym')
    if with_entity_version:
        qs = qs.prefetch_related(
            Prefetch('entity__entityversion_set', to_attr='entity_versions')
        )
    return qs


def is_entity_manager(user):
    return EntityManager.objects.filter(person__user=user).count() > 0


def has_perm_entity_manager(user):
    return user.has_perm('base.is_entity_manager')


def find_entities_with_descendants_from_entity_managers(entities_manager):
    entities_with_descendants = []
    entities_by_id = entity_version.build_current_entity_version_structure_in_memory()
    for entity_manager in entities_manager:
        entities_with_descendants.append(entity_manager.entity)
        entities_with_descendants += [
            ent_version.entity for ent_version in entities_by_id[entity_manager.entity_id].get('all_children')
        ]
    return entities_with_descendants

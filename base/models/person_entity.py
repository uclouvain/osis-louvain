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

from base.models import entity
from base.models import entity_version
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.osis_model_admin import OsisModelAdmin


class PersonEntityAdmin(OsisModelAdmin):
    list_display = ('person', 'entity', 'latest_entity_version_name', 'with_child')
    search_fields = ['person__first_name', 'person__last_name']
    raw_id_fields = ('person', 'entity',)

    def latest_entity_version_name(self, obj):
        entity_v = entity_version.get_last_version(obj.entity)
        if entity_v:
            entity_v_str = "{}".format(entity_v.acronym)
        else:
            entity_v_str = "Not found"
        return entity_v_str
    latest_entity_version_name.short_description = 'Latest entity version'


class PersonEntity(models.Model):
    person = models.ForeignKey('Person')
    entity = models.ForeignKey('Entity')
    with_child = models.BooleanField(default=False)

    class Meta:
        unique_together = ('person', 'entity',)

    def __str__(self):
        return u"%s" % self.person


def find_entities_by_person(person):
    person_entities = PersonEntity.objects.filter(person=person).select_related('entity')

    entities = set()
    entities |= {pers_ent.entity for pers_ent in person_entities if not pers_ent.with_child }
    entity_with_child = [pers_ent.entity for pers_ent in person_entities if pers_ent.with_child]
    if entity_with_child:
        entity_with_find_descendants = entity.find_descendants(entity_with_child, with_entities=True)
        entities |= set(entity_with_find_descendants) if entity_with_find_descendants else set()
    return list(entities)


def is_attached_entities(person, entity_queryset):
    admissible_entities = list(entity_queryset.values_list('pk', flat=True))

    qs = PersonEntity.objects.filter(person=person)
    if qs.filter(entity__in=admissible_entities).exists():
        return True
    elif qs.filter(entity__in=_entity_ancestors(entity_queryset), with_child=True).exists():
        return True
    else:
        return False


def _entity_ancestors(entity_list):
    ancestors = list(EntityVersion.objects.filter(entity__in=entity_list).exclude(parent__isnull=True)
                     .values_list('parent', flat=True))

    parents = Entity.objects.filter(pk__in=ancestors)
    if parents.exists():
        ancestors.extend(_entity_ancestors(parents))

    return ancestors or []

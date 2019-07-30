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
from django.utils.functional import cached_property
from reversion.admin import VersionAdmin

from base.models import entity_version
from base.models.entity_version import EntityVersion
from osis_common.models.osis_model_admin import OsisModelAdmin


class PersonEntityAdmin(VersionAdmin, OsisModelAdmin):
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
    person = models.ForeignKey('Person', on_delete=models.PROTECT)
    entity = models.ForeignKey('Entity', on_delete=models.CASCADE)
    with_child = models.BooleanField(default=False)

    class Meta:
        unique_together = ('person', 'entity',)

    def __str__(self):
        return u"%s" % self.person

    @cached_property
    def descendants(self):
        if not self.with_child:
            return {self.entity.id}

        # Create a set of all entity under the parent
        return set(row['entity_id'] for row in EntityVersion.objects.get_tree(self.entity))

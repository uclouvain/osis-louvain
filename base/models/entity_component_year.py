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
from reversion.admin import VersionAdmin

from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class EntityComponentYearAdmin(VersionAdmin, SerializableModelAdmin):
    list_display = ('entity_container_year', 'learning_component_year', 'repartition_volume',)
    search_fields = ['entity_container_year__learning_container_year__acronym']
    raw_id_fields = ('entity_container_year', 'learning_component_year')
    list_filter = ('entity_container_year__learning_container_year__academic_year',)


class EntityComponentYear(SerializableModel):
    external_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    entity_container_year = models.ForeignKey('EntityContainerYear')
    learning_component_year = models.ForeignKey('LearningComponentYear')
    repartition_volume = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return u"%s - %s" % (self.entity_container_year, self.learning_component_year)

    class Meta:
        unique_together = ('entity_container_year', 'learning_component_year', )


def find_by_learning_container_year(learning_container_yr):
    return EntityComponentYear.objects.filter(learning_component_year__learning_container_year=learning_container_yr)


def find_by_entity_container_years(entity_container_yrs, a_learning_component_year):
    return EntityComponentYear.objects.filter(entity_container_year__in=entity_container_yrs,
                                              learning_component_year=a_learning_component_year)

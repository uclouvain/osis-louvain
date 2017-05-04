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
from django.db import models
from base.models.enums import component_type
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class LearningUnitComponentAdmin(SerializableModelAdmin):
    list_display = ('learning_unit_year', 'learning_component_year', 'type', 'duration')
    fieldsets = ((None, {'fields': ('learning_unit_year', 'learning_component_year', 'type', 'duration',
                                    'coefficient_repetition')}),)
    raw_id_fields = ('learning_unit_year', )
    search_fields = ['learning_unit_year__acronym']


class LearningUnitComponent(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    learning_unit_year = models.ForeignKey('LearningUnitYear')
    learning_component_year = models.ForeignKey('LearningComponentYear', blank=True, null=True)
    type = models.CharField(max_length=25, blank=True, null=True, choices=component_type.COMPONENT_TYPES, db_index=True)
    duration = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    coefficient_repetition = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return u"%s - %s" % (self.type, self.learning_unit_year)

    class Meta:
        permissions = (
            ("can_access_learningunit", "Can access learning unit"),
        )

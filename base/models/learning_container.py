#############################################################################
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


class LearningContainerAdmin(VersionAdmin, SerializableModelAdmin):
    list_display = ('external_id',)
    search_fields = ['external_id', 'learningcontaineryear__acronym']


class LearningContainer(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    @property
    def most_recent_acronym(self):
        most_recent_container_year = self.learningcontaineryear_set.filter(learning_container_id=self.id)\
                                                                   .latest('academic_year__year')
        return most_recent_container_year.acronym

    def __str__(self):
        return u"%s" % self.external_id


def find_by_id(learning_container_id):
    return LearningContainer.objects.get(pk=learning_container_id)

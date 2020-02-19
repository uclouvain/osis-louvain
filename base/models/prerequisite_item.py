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
#############################################################################

from django.db import models, IntegrityError
from reversion.admin import VersionAdmin

from osis_common.models.osis_model_admin import OsisModelAdmin


class PrerequisiteItemAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('prerequisite', 'learning_unit', 'group_number', 'position')
    raw_id_fields = ('learning_unit', 'prerequisite')
    list_filter = ('prerequisite__learning_unit_year__academic_year',)
    search_fields = [
        'learning_unit__id',
        'prerequisite__id',
        'learning_unit__learningunityear__acronym',
        'learning_unit__learningunityear__specific_title',
        'prerequisite__learning_unit_year__acronym',
        'prerequisite__learning_unit_year__specific_title',
        'prerequisite__education_group_year__acronym',
        'prerequisite__education_group_year__title',
    ]


class PrerequisiteItem(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    learning_unit = models.ForeignKey("LearningUnit", on_delete=models.CASCADE)
    prerequisite = models.ForeignKey("Prerequisite", on_delete=models.CASCADE)

    group_number = models.PositiveIntegerField()
    position = models.PositiveIntegerField()

    def __str__(self):
        return "{} / {}".format(self.prerequisite, self.learning_unit.acronym)

    class Meta:
        unique_together = (
            ('prerequisite', 'group_number', 'position',),
        )

    def save(self, *args, **kwargs):
        if self.learning_unit == self.prerequisite.learning_unit_year.learning_unit:
            raise IntegrityError("A learning unit cannot be prerequisite to itself")
        super().save(*args, **kwargs)

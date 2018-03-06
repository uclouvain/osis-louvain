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

from base.models.academic_year import current_academic_year
from base.models.enums.learning_unit_periodicity import PERIODICITY_TYPES
from osis_common.models.auditable_serializable_model import AuditableSerializableModel, AuditableSerializableModelAdmin

LEARNING_UNIT_ACRONYM_REGEX_BASE = "^[BLMW][A-Z]{2,4}\d{4}"
LETTER_OR_DIGIT = "[A-Z0-9]"
STRING_END = "$"
LEARNING_UNIT_ACRONYM_REGEX_ALL = LEARNING_UNIT_ACRONYM_REGEX_BASE + LETTER_OR_DIGIT + "{0,1}" + STRING_END
LEARNING_UNIT_ACRONYM_REGEX_FULL = LEARNING_UNIT_ACRONYM_REGEX_BASE + STRING_END
LEARNING_UNIT_ACRONYM_REGEX_PARTIM = LEARNING_UNIT_ACRONYM_REGEX_BASE + LETTER_OR_DIGIT + STRING_END


class LearningUnitAdmin(AuditableSerializableModelAdmin):
    list_display = ('learning_container', 'acronym', 'title', 'start_year', 'end_year', 'changed')
    fieldsets = ((None, {
                    'fields': ('learning_container', 'acronym', 'title', 'start_year', 'end_year',
                               'periodicity', 'faculty_remark', 'other_remark')
                 }),)
    raw_id_fields = ('learning_container',)
    search_fields = ['acronym', 'title', 'learning_container__external_id']
    list_filter = ('periodicity', 'start_year')


class LearningUnit(AuditableSerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    learning_container = models.ForeignKey('LearningContainer', blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    acronym = models.CharField(max_length=15)
    title = models.CharField(max_length=255)
    start_year = models.IntegerField()
    end_year = models.IntegerField(blank=True, null=True)
    progress = None
    periodicity = models.CharField(max_length=20, blank=True, null=True, choices=PERIODICITY_TYPES)
    faculty_remark = models.TextField(blank=True, null=True)
    other_remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return u"%s - %s" % (self.acronym, self.title)

    def save(self, *args, **kwargs):
        if self.end_year and self.end_year < self.start_year:
            raise AttributeError("Start date should be before the end date")
        super(LearningUnit, self).save(*args, **kwargs)

    def is_past(self):
        return self.end_year and current_academic_year().year > self.end_year

    class Meta:
        permissions = (
            ("can_access_learningunit", "Can access learning unit"),
            ("can_edit_learningunit_date", "Can edit learning unit date"),
            ("can_edit_learningunit", "Can edit learning unit"),
            ("can_edit_learningunit_pedagogy", "Can edit learning unit pedagogy"),
            ("can_edit_learningunit_specification", "Can edit learning unit specification"),
            ("can_delete_learningunit", "Can delete learning unit"),
            ("can_propose_learningunit", "Can propose learning unit "),
            ("can_create_learningunit", "Can create learning unit"),
        )


def find_by_id(learning_unit_id):
    return LearningUnit.objects.get(pk=learning_unit_id)


def find_by_ids(learning_unit_ids):
    return LearningUnit.objects.filter(pk__in=learning_unit_ids)


def search(acronym=None):
    queryset = LearningUnit.objects

    if acronym:
        queryset = queryset.filter(acronym=acronym)

    return queryset

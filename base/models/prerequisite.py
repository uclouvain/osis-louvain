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
import itertools

from django.db import models
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from base.models.enums import prerequisite_operator
from base.models.enums.prerequisite_operator import OR, AND
from osis_common.models.osis_model_admin import OsisModelAdmin


class PrerequisiteAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('learning_unit_year', 'education_group_version')
    raw_id_fields = ('learning_unit_year', 'education_group_version')
    list_filter = ('education_group_version__offer__academic_year',)
    search_fields = ['learning_unit_year__acronym', 'education_group_version__offer__acronym',
                     'education_group_version__root_group__partial_acronym']
    readonly_fields = ('prerequisite_string',)


class Prerequisite(models.Model):
    external_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True
    )
    changed = models.DateTimeField(
        null=True,
        auto_now=True
    )

    learning_unit_year = models.ForeignKey(
        "LearningUnitYear", on_delete=models.CASCADE

    )
    # TODO : Remove this field after migration
    education_group_year = models.ForeignKey(
        "EducationGroupYear", on_delete=models.CASCADE,
        null=True, blank=True  # TODO :: remove this field after migration on education_group_version
    )
    education_group_version = models.ForeignKey(
        "program_management.EducationGroupVersion",
        on_delete=models.CASCADE,
        null=True  # TODO :: make this null=False after migration on education_group_version
    )
    main_operator = models.CharField(
        choices=prerequisite_operator.PREREQUISITES_OPERATORS,
        max_length=5,
        default=prerequisite_operator.AND
    )

    class Meta:
        unique_together = ('learning_unit_year', 'education_group_version')

    def __str__(self):
        return "{} / {}".format(
            self.education_group_version.offer if self.education_group_version else self.education_group_year,
            self.learning_unit_year
        )

    def save(self, *args, **kwargs):
        # TODO: Remove when migration is done (Field: education_group_year will be deleted)
        if self.education_group_version:
            self.education_group_year = self.education_group_version.offer
        return super().save(*args, **kwargs)

    @property
    def secondary_operator(self):
        return OR if self.main_operator == AND else AND

    @property
    def prerequisite_string(self):
        return self._get_acronyms_string()

    # FIXME Merge method with base/business/education_groups/excel.py and base/templatetags/prerequisite.py
    def _get_acronyms_string(self, display_method=None):
        prerequisite_items = self.prerequisiteitem_set.all().order_by('group_number', 'position')
        prerequisites_fragments = []
        for num_group, records_in_group in itertools.groupby(prerequisite_items, lambda rec: rec.group_number):
            list_records = list(records_in_group)
            predicate_format = "({})" if len(list_records) > 1 else "{}"
            join_secondary_operator = " {} ".format(_(self.secondary_operator))
            predicate = predicate_format.format(
                join_secondary_operator.join(
                    map(
                        lambda rec: display_method(rec, self.learning_unit_year.academic_year)
                        if display_method else rec.learning_unit.acronym,
                        list_records
                    )
                )
            )
            prerequisites_fragments.append(predicate)
        join_main_operator = " {} ".format(_(self.main_operator))
        return join_main_operator.join(prerequisites_fragments)

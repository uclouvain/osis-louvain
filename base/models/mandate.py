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

from base.models.enums import mandate_type as mandate_types
from osis_common.models.osis_model_admin import OsisModelAdmin


class MandateAdmin(OsisModelAdmin):
    list_display = ('education_group', 'function', 'qualification')

    raw_id_fields = ('education_group',)
    search_fields = ['education_group', 'function', 'external_id']


class Mandate(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    education_group = models.ForeignKey('EducationGroup', blank=True, null=True, on_delete=models.CASCADE)
    function = models.CharField(max_length=20, choices=mandate_types.MANDATE_TYPES)
    qualification = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return "{} {}".format(self.education_group, self.function)

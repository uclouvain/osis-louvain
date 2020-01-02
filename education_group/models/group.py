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
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from osis_common.models.osis_model_admin import OsisModelAdmin


class GroupAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('start_year', 'end_year', 'changed')
    search_fields = ('groupyear__acronym', 'groupyear__partial_acronym',)


class Group(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    start_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('Start academic year'),
        related_name='group_start_years',
        on_delete=models.PROTECT
    )
    end_year = models.ForeignKey(
        'base.AcademicYear',
        blank=True,
        null=True,
        verbose_name=_('End academic year'),
        related_name='group_end_years',
        on_delete=models.PROTECT
    )

    def save(self, *args, **kwargs):
        if self.end_year and self.start_year.year > self.end_year.year:
            raise AttributeError(_('End year must be greater than the start year, or equal'))

        super().save(*args, **kwargs)

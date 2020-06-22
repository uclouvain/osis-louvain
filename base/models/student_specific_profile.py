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
from django.utils.translation import gettext_lazy as _

from base.models.enums import peps_type
from osis_common.models.osis_model_admin import OsisModelAdmin


class StudentSpecificProfileAdmin(OsisModelAdmin):
    list_display = ('student', 'guide', 'changed',)
    list_filter = ('type', 'subtype_disability', 'subtype_sport')
    search_fields = ['guide__first_name', 'guide__last_name', 'student']


class StudentSpecificProfile(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    student = models.OneToOneField('Student', on_delete=models.PROTECT)
    type = models.CharField(
        max_length=20,
        choices=peps_type.PepsTypes.choices(),
        null=False
    )
    subtype_disability = models.CharField(
        max_length=20,
        choices=peps_type.HtmSubtypes.choices(),
        blank=True,
        null=False,
        verbose_name=_('Sub type Disability')
    )
    subtype_sport = models.CharField(
        max_length=20,
        choices=peps_type.SportSubtypes.choices(),
        blank=True,
        null=False,
        verbose_name=_('Sub type Sport')
    )
    guide = models.ForeignKey('Person', on_delete=models.PROTECT, verbose_name=_('Guide'), blank=True, null=True)
    arrangement_additional_time = models.BooleanField(default=False, verbose_name=_('Arrangement additional time'))
    arrangement_appropriate_copy = models.BooleanField(default=False, verbose_name=_('Arrangement appropriate copy'))
    arrangement_other = models.BooleanField(default=False, verbose_name=_('Arrangement other'))
    arrangement_specific_locale = models.BooleanField(default=False, verbose_name=_('Arrangement specific locale'))

    class Meta:
        ordering = ("student", "guide__last_name", "guide__first_name")

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
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from osis_common.models.osis_model_admin import OsisModelAdmin


class HopsAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('ares_study', 'ares_graca', 'ares_ability', 'changed')
    list_filter = ('ares_study', )
    raw_id_fields = (
        'education_group_year'
    )
    search_fields = ['ares_study']


class Hops(models.Model):
    # HOPS means "Habilitations et Offre Programmée de l’enseignement Supérieur".
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    education_group_year = models.OneToOneField('base.EducationGroupYear', on_delete=models.CASCADE)

    ares_study = models.IntegerField(
        verbose_name=_('ARES study code'),
        validators=[MinValueValidator(1), MaxValueValidator(9999)],
    )

    ares_graca = models.IntegerField(
        verbose_name=_('ARES-GRACA'),
        validators=[MinValueValidator(1), MaxValueValidator(9999)],
    )

    ares_ability = models.IntegerField(
        verbose_name=_('ARES ability'),
        validators=[MinValueValidator(1), MaxValueValidator(9999)],

    )

    def __str__(self):
        return str(self.ares_study) if self.ares_study else ''

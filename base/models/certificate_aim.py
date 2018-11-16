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
from django.utils.translation import ugettext_lazy as _
from osis_common.models.osis_model_admin import OsisModelAdmin


class CertificateAimAdmin(OsisModelAdmin):
    list_display = ('section', 'description', 'changed')
    search_fields = ('description',)
    list_filter = ('section',)


class CertificateAim(models.Model):
    external_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
    )

    changed = models.DateTimeField(
        null=True,
        auto_now=True,
    )

    code = models.PositiveIntegerField(
        verbose_name=_("aim number"),
        db_index=True,
        unique=True,
    )

    section = models.PositiveIntegerField(
        verbose_name=_("section"),
        db_index=True,
    )

    description = models.CharField(
        verbose_name=_("Description"),
        max_length=1024,
        db_index=True,
        unique=True,
    )

    class Meta:
        ordering = ('section', 'code')

    def __str__(self):
        return "{} - {} {}".format(self.section, self.code, self.description)

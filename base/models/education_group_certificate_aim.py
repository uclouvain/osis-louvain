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
from reversion.admin import VersionAdmin

from base.models.certificate_aim import CertificateAim
from base.models.education_group_year import EducationGroupYear
from osis_common.models.osis_model_admin import OsisModelAdmin


class EducationGroupCertificateAimAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('education_group_year', 'certificate_aim', 'changed')
    search_fields = ('education_group_year__acronym', 'certificate_aim__description')
    list_filter = ('certificate_aim__section', 'education_group_year__academic_year')
    ordering = ('education_group_year__acronym',)


class EducationGroupCertificateAim(models.Model):
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

    education_group_year = models.ForeignKey(
        EducationGroupYear,
        on_delete=models.CASCADE,
    )

    certificate_aim = models.ForeignKey(
        CertificateAim,
        on_delete=models.PROTECT,
    )

    class Meta:
        unique_together = ('education_group_year', 'certificate_aim',)

    def __str__(self):
        return "{} - {}".format(self.education_group_year, self.certificate_aim)

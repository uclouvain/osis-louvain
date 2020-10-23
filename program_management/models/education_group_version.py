##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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


class EducationGroupVersionAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('offer', 'version_name', 'root_group', 'is_transition')
    list_filter = ('is_transition', 'offer__academic_year')
    search_fields = ('offer__acronym', 'root_group__partial_acronym', 'version_name')


class StandardEducationGroupVersionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(version_name='')


class EducationGroupVersion(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    is_transition = models.BooleanField(verbose_name=_('Transition'))
    version_name = models.CharField(
        blank=True,
        max_length=25,
        verbose_name=_('Version name')
    )
    root_group = models.OneToOneField(
        'education_group.GroupYear',
        unique=True,
        verbose_name=_('Root group'),
        on_delete=models.PROTECT,
        related_name='educationgroupversion'
    )
    offer = models.ForeignKey(
        'base.EducationGroupYear',
        blank=True, null=True,
        verbose_name=_('Offer'),
        on_delete=models.PROTECT
    )
    title_fr = models.CharField(
        blank=True, null=True,
        max_length=240,
        verbose_name=_("Title in French")
    )
    title_en = models.CharField(
        blank=True, null=True,
        max_length=240,
        verbose_name=_("Title in English")
    )

    objects = models.Manager()
    standard = StandardEducationGroupVersionManager()

    def __str__(self):
        return "{} ({})".format(self.offer, self.version_name) if self.version_name else str(self.offer)

    class Meta:
        unique_together = ('version_name', 'offer', 'is_transition')
        default_manager_name = 'objects'

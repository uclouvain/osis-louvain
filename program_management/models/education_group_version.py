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
from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from base.utils.constants import YES, NO
from osis_common.models.osis_model_admin import OsisModelAdmin


def fill_from_past_year(modeladmin, request, queryset):
    from program_management.ddd.command import FillTreeVersionContentFromPastYearCommand
    from program_management.ddd.service.write import bulk_fill_program_tree_version_content_service_from_past_year
    cmds = []
    qs = queryset.select_related("offer", "root_group")
    for obj in qs:
        cmd = FillTreeVersionContentFromPastYearCommand(
            to_year=obj.offer.academic_year.year,
            to_offer_acronym=obj.offer.acronym,
            to_version_name=obj.version_name,
            to_transition_name=obj.transition_name
        )
        cmds.append(cmd)
    result = bulk_fill_program_tree_version_content_service_from_past_year.\
        bulk_fill_program_tree_version_content_from_past_year(cmds)
    modeladmin.message_user(request, "{} programs have been filled".format(len(result)))


fill_from_past_year.short_description = _("Fill program tree content from last year")


class StandardListFilter(admin.SimpleListFilter):
    title = _('Version')

    parameter_name = 'standard'

    def lookups(self, request, model_admin):
        return (
            (YES, _("Standard")),
            (NO, _("Particular"))
        )

    def queryset(self, request, queryset):
        from program_management.ddd.domain import program_tree_version
        if self.value() == YES:
            return queryset.filter(version_name=program_tree_version.STANDARD)
        if self.value() == NO:
            return queryset.exclude(version_name=program_tree_version.STANDARD)
        return queryset


class TransitionListFilter(admin.SimpleListFilter):
    title = _('Transition')

    parameter_name = 'transition'

    def lookups(self, request, model_admin):
        return (
            (YES, _("Yes")),
            (NO, _("No"))
        )

    def queryset(self, request, queryset):
        from program_management.ddd.domain import program_tree_version
        if self.value() == YES:
            return queryset.exclude(transition_name=program_tree_version.NOT_A_TRANSITION)
        if self.value() == NO:
            return queryset.filter(transition_name=program_tree_version.NOT_A_TRANSITION)
        return queryset


class EducationGroupVersionAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('offer', 'version_name', 'root_group', 'transition_name')
    list_filter = (StandardListFilter, TransitionListFilter, 'offer__academic_year',)
    search_fields = ('offer__acronym', 'root_group__partial_acronym', 'version_name')
    actions = [fill_from_past_year]


class StandardEducationGroupVersionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(version_name='')


class EducationGroupVersion(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    transition_name = models.CharField(
        blank=True,
        max_length=25,
        verbose_name=_('Transition name'),
        default=''
    )
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
        offer_name = self.offer.acronym
        if self.version_name and self.transition_name:
            offer_name += '[{}-{}]'.format(self.version_name, self.transition_name)
        elif self.version_name:
            offer_name += '[{}]'.format(self.version_name)
        elif self.transition_name:
            offer_name += '[{}]'.format(self.transition_name)
        offer_name += ' - {}'.format(self.offer.academic_year)
        return offer_name

    class Meta:
        unique_together = ('version_name', 'offer', 'transition_name')
        default_manager_name = 'objects'

    def version_label(self):
        if self.version_name and self.transition_name:
            return '[{}-{}]'.format(self.version_name, self.transition_name)
        elif self.version_name or self.transition_name:
            return '[{}]'.format(self.version_name if self.version_name else self.transition_name)
        return ''

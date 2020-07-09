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
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _, ngettext
from reversion.admin import VersionAdmin

from base.business.education_groups import shorten
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.enums.education_group_types import TrainingType
from osis_common.models.serializable_model import SerializableModelAdmin, SerializableModel, SerializableModelManager


class EducationGroupAdmin(VersionAdmin, SerializableModelAdmin):
    list_display = ('most_recent_acronym', 'start_year', 'end_year', 'changed')
    search_fields = ('educationgroupyear__acronym', 'educationgroupyear__partial_acronym')

    actions = [
        'apply_education_group_year_postponement'
    ]

    def apply_education_group_year_postponement(self, request, queryset):
        # Potential circular imports
        from base.business.education_groups.automatic_postponement import EducationGroupAutomaticPostponementToN6
        from base.views.common import display_success_messages, display_error_messages

        result, errors = EducationGroupAutomaticPostponementToN6(queryset).postpone()
        count = len(result)
        display_success_messages(
            request, ngettext(
                "%(count)d education group has been postponed with success.",
                "%(count)d education groups have been postponed with success.", count
            ) % {'count': count}
        )
        if errors:
            display_error_messages(request, "{} : {}".format(
                _("The following education groups ended with error"),
                ", ".join([str(error) for error in errors])
            ))

    apply_education_group_year_postponement.short_description = _("Apply postponement on education group year")


class EducationGroupManager(SerializableModelManager):
    def having_related_training(self, **kwargs):
        # .distinct() is necessary if there is more than one training egy related to an education_group
        return self.filter(
            educationgroupyear__education_group_type__category=education_group_categories.TRAINING,
            **kwargs
        ).distinct()


class EducationGroup(SerializableModel):
    objects = EducationGroupManager()
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    start_year = models.ForeignKey(
        'AcademicYear',
        verbose_name=_('Start academic year'),
        related_name='start_years',
        on_delete=models.PROTECT
    )
    end_year = models.ForeignKey(
        'AcademicYear',
        blank=True,
        null=True,
        verbose_name=_('Last year of organization'),
        related_name='end_years',
        on_delete=models.PROTECT
    )

    @property
    def most_recent_acronym(self):
        most_recent_education_group = self.educationgroupyear_set.filter(education_group_id=self.id) \
            .latest('academic_year__year')
        return most_recent_education_group.acronym

    def __str__(self):
        return "{}".format(self.id)

    class Meta:
        permissions = (
            ("add_training", "Can add training"),
            ("add_minitraining", "Can add mini-training"),
            ("add_group", "Can add group"),
            ("delete_training", "Can delete training"),
            ("delete_minitraining", "Can delete mini-training"),
            ("delete_group", "Can delete group"),
            ("change_commonpedagogyinformation", "Can change common pedagogy information"),
            ("change_pedagogyinformation", "Can change pedagogy information"),
            ("change_link_data", "Can change link data"),
        )
        verbose_name = _("Education group")

    def clean(self):
        # Check end_year should be greater of equals to start_year
        if self.start_year and self.end_year:
            if self.start_year.year > self.end_year.year:
                raise ValidationError({
                    'end_year': _("%(max)s must be greater or equals than %(min)s") % {
                        "max": _("Last year of organization").title(),
                        "min": _("Start"),
                    }
                })

        self._check_end_year_constraints_on_2m()

        # Check if end_year could be set according to protected data
        if self.end_year:
            shorten.check_education_group_end_date(self, self.end_year)

    def _check_end_year_constraints_on_2m(self):
        qs = self.educationgroupyear_set.all().filter(
            education_group_type__name__in=TrainingType.finality_types() + TrainingType.root_master_2m_types()
        ).select_related('education_group_type')

        for education_group_year in qs:
            if education_group_year.type in TrainingType.finality_types():
                self._check_end_year_finality_are_in_range_of_root_2m(education_group_year)
            elif education_group_year.type in TrainingType.root_master_2m_types() and self.end_year is not None:
                self._check_end_year_root_2m_cover_all_finalities(education_group_year)

    def _check_end_year_finality_are_in_range_of_root_2m(self, finality_egy):
        qs = EducationGroupYear.hierarchy.filter(pk=finality_egy.pk) \
            .get_parents().filter(education_group_type__name__in=TrainingType.root_master_2m_types())

        if self.end_year is None:
            qs = qs.filter(education_group__end_year__isnull=False)
        else:
            qs = qs.filter(education_group__end_year__lt=self.end_year)

        for invalid_root_2m in qs:
            raise ValidationError({
                'end_year':
                    _('The end date must be less or equals to the root %(acronym)s') %
                    {'acronym': invalid_root_2m.acronym}
            })

    def _check_end_year_root_2m_cover_all_finalities(self, root_2m_egy):
        qs = EducationGroupYear.hierarchy.filter(pk=root_2m_egy.pk) \
            .get_children() \
            .filter(
            Q(education_group__end_year__gt=self.end_year) | Q(education_group__end_year__isnull=True),
            education_group_type__name__in=TrainingType.finality_types(),
        )

        for invalid_finality in qs:
            raise ValidationError({
                'end_year':
                    _('The end date must be greater or equals to the finality %(acronym)s') %
                    {'acronym': invalid_finality.acronym}
            })

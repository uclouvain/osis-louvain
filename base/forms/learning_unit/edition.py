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
from django import forms
from django.utils.translation import gettext_lazy as _

from attribution.models.tutor_application import TutorApplication
from base.business.learning_units.edition import edit_learning_unit_end_date
from base.forms.learning_unit.learning_unit_postponement import LearningUnitPostponementForm
from base.forms.utils.choice_field import BLANK_CHOICE_DISPLAY, NO_PLANNED_END_DISPLAY
from base.models.academic_year import AcademicYear
from base.models.enums import learning_unit_year_subtypes
from base.models.proposal_learning_unit import find_by_learning_unit
# TODO Convert it in ModelForm
from education_group.calendar.education_group_extended_daily_management import \
    EducationGroupExtendedDailyManagementCalendar


class LearningUnitEndDateForm(forms.Form):
    EMPTY_LABEL = BLANK_CHOICE_DISPLAY
    REQUIRED = True
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.none(),
                                           label=_('Last year of organization')
                                           )

    def __init__(self, data, learning_unit_year, *args, max_year=None, person=None, **kwargs):
        self.learning_unit = learning_unit_year.learning_unit
        self.learning_unit_year = learning_unit_year
        self.person = person
        super().__init__(data, *args, **kwargs)
        self.fields['academic_year'].empty_label = self.EMPTY_LABEL
        self.fields['academic_year'].required = self.REQUIRED
        end_year = self.learning_unit.end_year
        self.start_year = self.learning_unit.start_year

        self._set_initial_value(end_year)

        try:
            self.fields['academic_year'].queryset = self._get_academic_years(max_year)
        except ValueError:
            self.fields['academic_year'].disabled = True

        if max_year:
            self.fields['academic_year'].required = True

    def _set_initial_value(self, end_year):
        self.fields['academic_year'].initial = end_year

    def _get_academic_years(self, max_year):
        pass

    def save(self, update_learning_unit_year=True):
        learning_unit_full_instance = None
        if self.learning_unit_year.subtype == learning_unit_year_subtypes.PARTIM:
            learning_unit_full_instance = self.learning_unit_year.parent.learning_unit
        postponement_form = LearningUnitPostponementForm(
            person=self.person,
            start_postponement=self.learning_unit_year.academic_year,
            learning_unit_instance=self.learning_unit_year.learning_unit,
            learning_unit_full_instance=learning_unit_full_instance,
            external=self.learning_unit_year.is_external(),
        )
        if postponement_form.is_valid():
            postponement_form.save()
        return edit_learning_unit_end_date(
            self.learning_unit,
            self.cleaned_data['academic_year'],
            update_learning_unit_year
        )


class LearningUnitProposalEndDateForm(LearningUnitEndDateForm):
    EMPTY_LABEL = None

    def __init__(self, data, learning_unit_year, *args, max_year=None, person=None, **kwargs):
        super().__init__(data, learning_unit_year, *args, max_year=max_year, person=person, **kwargs)
        self.fields['academic_year'].widget.attrs['readonly'] = 'readonly'

    def _get_academic_years(self, max_year):
        if not has_proposal(self.learning_unit) and self.learning_unit.is_past():
            raise ValueError(
                'Learning_unit.end_year {} cannot be less than the current academic_year'.format(
                    self.learning_unit.end_year)
            )

        self.luy_current_year = self.learning_unit_year.academic_year.year
        # Allow previous year as last organisation year for suppression proposal
        return AcademicYear.objects.filter(year=self.luy_current_year - 1)

    def clean_academic_year(self):
        return AcademicYear.objects.get(year=self.luy_current_year - 1)


class LearningUnitDailyManagementEndDateForm(LearningUnitEndDateForm):
    EMPTY_LABEL = NO_PLANNED_END_DISPLAY
    REQUIRED = False

    def _get_academic_years(self, max_year):
        # only select Extended Calendar because central AND faculty have to be able to put the end_date until N+6
        # dropdown end_year is different of permission
        target_years_opened = EducationGroupExtendedDailyManagementCalendar().get_target_years_opened()

        self.luy_current_year = self.learning_unit_year.academic_year.year

        learning_container = self.learning_unit_year.learning_container_year.learning_container
        if self.learning_unit_year.is_full():
            academic_year_learning_container_year = self.learning_unit_year.learning_container_year.academic_year
            applications = TutorApplication.objects.filter(
                learning_container_year__learning_container=learning_container,
                learning_container_year__academic_year__year__gte=academic_year_learning_container_year.year
            ).order_by('learning_container_year__academic_year__year')
            if not max_year and applications:
                max_year = applications.first().learning_container_year.academic_year.year
        else:
            lu_parent = self.learning_unit.parent
            max_year = lu_parent.end_year.year if lu_parent and lu_parent.end_year else None
        academic_years = AcademicYear.objects.filter(year__gte=self.luy_current_year, year__in=target_years_opened)
        return academic_years.filter(year__lte=max_year) if max_year else academic_years


def has_proposal(learning_unit):
    if find_by_learning_unit(learning_unit):
        return True
    return False

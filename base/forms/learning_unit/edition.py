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
from django import forms
from django.utils.translation import ugettext_lazy as _

from base.business.learning_units.edition import filter_biennial, edit_learning_unit_end_date
from base.models import academic_year
from base.models.academic_year import AcademicYear, compute_max_academic_year_adjournment


# TODO Convert it in ModelForm
class LearningUnitEndDateForm(forms.Form):
    academic_year = forms.ModelChoiceField(required=False,
                                           queryset=AcademicYear.objects.none(),
                                           empty_label=_('no planned end'),
                                           label=_('Academic end year')
                                           )

    def __init__(self, data, learning_unit_year, *args, max_year=None, **kwargs):
        self.learning_unit = learning_unit_year.learning_unit
        self.learning_unit_year = learning_unit_year
        super().__init__(data, *args, **kwargs)
        end_year = self.learning_unit.end_year

        self._set_initial_value(end_year)

        try:
            queryset = self._get_academic_years(max_year)

            periodicity = self.learning_unit_year.periodicity
            self.fields['academic_year'].queryset = filter_biennial(queryset, periodicity)
        except ValueError:
            self.fields['academic_year'].disabled = True

        if max_year:
            self.fields['academic_year'].required = True

    def _set_initial_value(self, end_year):
        try:
            self.fields['academic_year'].initial = AcademicYear.objects.get(year=end_year)
        except (AcademicYear.DoesNotExist, AcademicYear.MultipleObjectsReturned):
            self.fields['academic_year'].initial = None

    def _get_academic_years(self, max_year):
        current_academic_year = academic_year.current_academic_year()
        min_year = current_academic_year.year

        if not max_year:
            max_year = compute_max_academic_year_adjournment()

        if self.learning_unit.start_year > min_year:
            min_year = self.learning_unit.start_year

        if self.learning_unit.is_past():
            raise ValueError(
                'Learning_unit.end_year {} cannot be less than the current academic_year {}'.format(
                    self.learning_unit.end_year, current_academic_year)
            )

        if min_year > max_year:
            raise ValueError('Learning_unit {} cannot be modify'.format(self.learning_unit))

        return academic_year.find_academic_years(start_year=min_year, end_year=max_year)

    def save(self, update_learning_unit_year=True):
        return edit_learning_unit_end_date(self.learning_unit, self.cleaned_data['academic_year'],
                                           update_learning_unit_year)

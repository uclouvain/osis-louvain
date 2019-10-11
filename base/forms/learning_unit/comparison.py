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
from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from base.models.academic_year import AcademicYear
from base.models.academic_year import starting_academic_year

LIMIT_OF_CHOICES = 2


class SelectComparisonYears(forms.Form):

    def __init__(self, *args, **kwargs):
        academic_year = kwargs.pop('academic_year', None)
        self.search_form = kwargs.pop('search_form', None)

        super(SelectComparisonYears, self).__init__(*args, **kwargs)
        if academic_year is None:
            academic_year = starting_academic_year()

        years = AcademicYear.objects.filter(
            Q(year=academic_year.year + 1) | Q(year=academic_year.year - 1)).order_by('year')
        choices = _get_choices(years, academic_year)
        initial_value = _get_initial(choices)
        self.fields['academic_years'] = forms.ChoiceField(
            widget=forms.RadioSelect,
            required=True,
            label=_('Choose academic years'),
        )
        if choices:
            self.fields['academic_years'].choices = choices

        if initial_value:
            self.fields['academic_years'].initial = initial_value


def _get_choices(academic_years, current_academic_year):
    if len(academic_years) == LIMIT_OF_CHOICES:
        return [
            (academic_years[0].year, str(academic_years[0]) + ' / ' + str(current_academic_year)),
            (academic_years[1].year, str(current_academic_year) + ' / ' + str(academic_years[1]))
        ]
    return None


def _get_initial(choices):
    if choices:
        return choices[0]
    return None

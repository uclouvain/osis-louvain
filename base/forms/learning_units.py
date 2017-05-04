##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from base import models as mdl
from django.core.exceptions import ValidationError


class LearningUnitYearForm(forms.Form):
    academic_year = forms.CharField(max_length=10, required=False)
    acronym = keyword = forms.CharField(widget=forms.TextInput(attrs={'size': '10', 'class': 'form-control'}),
                                        max_length=20, required=False)

    def clean_acronym(self):
        MIN_ACRONYM_LENGTH = 3
        data_cleaned = self.cleaned_data.get('acronym')
        data_cleaned = _treat_empty_or_str_none_as_none(data_cleaned)
        if data_cleaned and len(data_cleaned) < MIN_ACRONYM_LENGTH:
            raise ValidationError('LU_ERRORS_INVALID_SEARCH')
        return data_cleaned

    def clean(self):
        clean_data = _clean_data(self.cleaned_data)
        is_valid_search(**clean_data)
        return clean_data

    def get_learning_units(self):
        clean_data = self.cleaned_data

        return mdl.learning_unit_year.search(academic_year_id=clean_data.get('academic_year'),
                                             acronym=clean_data.get('acronym'),
                                             title=clean_data.get('keyword'))\
                                     .select_related('academic_year')\
                                     .order_by('academic_year__year', 'acronym')


def is_valid_search(**search_filter):
    academic_year = search_filter.get('academic_year')
    learning_unit_acronym = search_filter.get('acronym')
    keyword = search_filter.get('keyword')

    if academic_year and learning_unit_acronym:
        return True
    elif academic_year and keyword:
        return True
    elif learning_unit_acronym:
        return True

    raise ValidationError('LU_ERRORS_INVALID_SEARCH')


def _clean_data(datas_to_clean):
    return {key: _treat_empty_or_str_none_as_none(value) for (key, value) in datas_to_clean.items()}


def _treat_empty_or_str_none_as_none(data):
    return None if not data or data == "NONE" else data


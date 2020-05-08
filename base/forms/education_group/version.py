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
from django.forms import TextInput
from django.utils.translation import gettext_lazy as _

import base.views.education_groups.create
from base.business.education_groups.create import create_initial_group_element_year_structure
from base.forms.utils.choice_field import BLANK_CHOICE
from base.models import academic_year
from base.models.academic_year import compute_max_academic_year_adjournment
from program_management.ddd.service.create_program_tree_version import report_specific_version_creation, \
    create_specific_version


class SpecificVersionForm(forms.Form):
    version_name = forms.CharField(max_length=15, required=True, label=_('Acronym of version'), widget=TextInput(attrs={
        'onchange': 'validate_version_name()'
    }))
    title = forms.CharField(max_length=100, required=False, label=_('Full title of the french version'))
    title_english = forms.CharField(max_length=100, required=False, label=_('Full title of the english version'))
    end_year = forms.ChoiceField(required=False, label=_('This version exists until'))

    def __init__(self, *args, **kwargs):
        self.save_type = kwargs.pop('save_type')
        self.education_group_years_list = []
        self.person = kwargs.pop('person')
        self.education_group_year = kwargs.pop('education_group_year')
        self.max_year = academic_year.find_academic_year_by_year(compute_max_academic_year_adjournment() + 1).year
        choices_years = [(x, x) for x in range(self.education_group_year.academic_year.year, self.max_year)]
        super().__init__(*args, **kwargs)
        self.fields["end_year"].choices = BLANK_CHOICE + choices_years

    def save(self):
        end_postponement = self.max_year if not self.cleaned_data['end_year'] else self.cleaned_data['end_year']
        data = {
            "version_name": self.cleaned_data.get("version_name"),
            "title_fr": self.cleaned_data.get("title"),
            "title_en": self.cleaned_data.get("title_english")
        }
        if self.save_type == "new_version":
            create_specific_version(data, self.education_group_year)
            education_group_years_list = [self.education_group_year]
            self.education_group_years_list = report_specific_version_creation(
                data, self.education_group_year, end_postponement, education_group_years_list
            )
        if self.save_type == "attach":
            education_group_years_list = []
            last_old_version = base.views.education_groups.create.find_last_existed_version(
                self.education_group_year, self.cleaned_data["version_name"]
            )
            self.education_group_years_list = report_specific_version_creation(
                data, last_old_version.offer, end_postponement, education_group_years_list
            )
        create_initial_group_element_year_structure(self.education_group_years_list)

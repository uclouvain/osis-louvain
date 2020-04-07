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
from django.core.exceptions import ValidationError
from django.forms import TextInput
from django.utils.translation import gettext_lazy as _

from base.business import event_perms
from base.business.education_groups.create import create_initial_group_element_year_structure
from base.forms.utils.choice_field import BLANK_CHOICE_DISPLAY
from base.models import academic_year
from base.models.academic_year import AcademicYear, compute_max_academic_year_adjournment
from program_management.ddd.repositories import load_specific_version
from program_management.models.education_group_version import EducationGroupVersion


class SpecificVersionForm(forms.Form):
    version_name = forms.CharField(max_length=15, required=True, label=_('Acronym of version'), widget=TextInput(attrs={
        'onchange': 'validate_version_name()'
    }))
    title = forms.CharField(max_length=100, required=False, label=_('Full title of the french version'))
    title_english = forms.CharField(max_length=100, required=False, label=_('Full title of the english version'))
    end_year = forms.ModelChoiceField(queryset=AcademicYear.objects.none(), required=False,
                                      label=_('This version exists until'), empty_label=BLANK_CHOICE_DISPLAY)

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('person')
        self.education_group_year = kwargs.pop('education_group_year')
        super().__init__(*args, **kwargs)
        try:
            event_perm = event_perms.generate_event_perm_creation_specific_version(self.person)
            self.fields["end_year"].queryset = event_perm.get_academic_years()
            self.fields["end_year"].initial = self.education_group_year.academic_year
        except ValueError:
            self.fields['end_year'].disabled = True

    def clean_version_name(self):
        version_name = self.education_group_year.acronym + self.cleaned_data["version_name"]
        if load_specific_version.check_existing_version(version_name, self.education_group_year.id):
            raise ValidationError(_("Acronym already exists in %(academic_year)s") % {
                "academic_year": self.education_group_year.academic_year})
        return version_name.upper()

    def save(self, education_group_year):
        max_year = academic_year.find_academic_year_by_year(compute_max_academic_year_adjournment() + 1).year
        end_postponement = max_year if not self.cleaned_data['end_year'] else self.cleaned_data['end_year'].year
        self._create_specific_version(education_group_year)
        education_group_years_list = self._report_specific_version_creation(education_group_year, end_postponement)
        create_initial_group_element_year_structure(education_group_years_list)

    def _report_specific_version_creation(self, education_group_year, end_postponement):
        education_group_years_list = [education_group_year]
        education_group_year = education_group_year.next_year()
        if education_group_year:
            while education_group_year.academic_year.year <= end_postponement or not education_group_year:
                education_group_years_list.append(education_group_year)
                self._create_specific_version(education_group_year)
                education_group_year = education_group_year.next_year()
                if not education_group_year:
                    break
        return education_group_years_list

    def _create_specific_version(self, education_group_year):
        version_standard = EducationGroupVersion.objects.get(
            offer=education_group_year, version_name="", is_transition=False
        )
        new_groupyear = version_standard.root_group
        new_groupyear.pk = None
        new_groupyear.save()
        new_education_group_version = EducationGroupVersion(
            version_name=self.cleaned_data["version_name"],
            title_fr=self.cleaned_data["title"],
            title_en=self.cleaned_data["title_english"],
            offer=education_group_year,
            is_transition=False,
            root_group=new_groupyear
        )
        new_education_group_version.save()
        return new_education_group_version

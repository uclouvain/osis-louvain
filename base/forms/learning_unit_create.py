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
import re

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.forms.bootstrap import BootstrapForm
from base.models.campus import find_administration_campuses
from base.models.entity_version import find_main_entities_version, find_main_entities_version_filtered_by_person
from base.models.enums import entity_container_year_link_type
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES, INTERNSHIP
from base.models.enums.learning_unit_periodicity import PERIODICITY_TYPES
from base.models.enums.learning_unit_year_quadrimesters import LEARNING_UNIT_YEAR_QUADRIMESTERS
from reference.models.language import find_all_languages


MAX_RECORDS = 1000
EMPTY_FIELD = "---------"


def create_learning_container_year_type_list():
    return ((None, EMPTY_FIELD),) + LEARNING_CONTAINER_YEAR_TYPES


class EntitiesVersionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.acronym


class CreateLearningUnitYearForm(BootstrapForm):
    acronym = forms.CharField(widget=forms.TextInput(attrs={'maxlength': "15", 'required': True}))
    academic_year = forms.ModelChoiceField(queryset=mdl.academic_year.find_academic_years(), required=True,
                                           empty_label=_('all_label'))
    status = forms.CharField(required=False, widget=forms.CheckboxInput())
    internship_subtype = forms.ChoiceField(choices=((None, EMPTY_FIELD),) +
                                           mdl.enums.internship_subtypes.INTERNSHIP_SUBTYPES,
                                           required=False)
    credits = forms.DecimalField(decimal_places=2)
    title = forms.CharField(widget=forms.TextInput(attrs={'required': True}))
    title_english = forms.CharField(required=False, widget=forms.TextInput())
    session = forms.ChoiceField(choices=((None, EMPTY_FIELD),) +
                                mdl.enums.learning_unit_year_session.LEARNING_UNIT_YEAR_SESSION,
                                required=False)
    subtype = forms.CharField(widget=forms.HiddenInput())
    first_letter = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'text-center',
                                                                                 'maxlength': "1",
                                                                                 'readonly': 'readonly'}))
    container_type = forms.ChoiceField(choices=lazy(create_learning_container_year_type_list, tuple),
                                       widget=forms.Select(attrs={'onchange': 'showInternshipSubtype(this.value)'}))
    faculty_remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    other_remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    periodicity = forms.CharField(widget=forms.Select(choices=PERIODICITY_TYPES))
    quadrimester = forms.CharField(
                        widget=forms.Select(choices=((None, EMPTY_FIELD),) + LEARNING_UNIT_YEAR_QUADRIMESTERS),
                        required=False
    )
    campus = forms.ModelChoiceField(queryset=find_administration_campuses(),
                                    widget=forms.Select(attrs={'onchange': 'setFirstLetter()'}))

    requirement_entity = EntitiesVersionChoiceField(
        find_main_entities_version().none(),
        widget=forms.Select(
            attrs={'onchange': 'showAdditionalEntity(this.value, "id_additional_entity_1")'}
        )
    )

    allocation_entity = EntitiesVersionChoiceField(find_main_entities_version(),
                                                   required=False,
                                                   widget=forms.Select(attrs={'id': 'allocation_entity'}))

    additional_entity_1 = EntitiesVersionChoiceField(
        find_main_entities_version(),
        required=False,
        widget=forms.Select(
            attrs={'onchange': 'showAdditionalEntity(this.value, "id_additional_entity_2")', 'disable': 'disable'}
        )
    )

    additional_entity_2 = EntitiesVersionChoiceField(find_main_entities_version(),
                                                     required=False,
                                                     widget=forms.Select(attrs={'disable': 'disable'}))

    language = forms.ModelChoiceField(find_all_languages(), empty_label=None)

    acronym_regex = "^[BLMW][A-Z]{2,4}\d{4}$"

    def __init__(self, person, *args, **kwargs):
        super(CreateLearningUnitYearForm, self).__init__(*args, **kwargs)
        # When we create a learning unit, we can only select requirement entity which are attached to the person
        self.fields["requirement_entity"].queryset = find_main_entities_version_filtered_by_person(person)

    def clean_acronym(self):
        data_cleaned = self.data.get('first_letter')+self.cleaned_data.get('acronym')
        if data_cleaned:
            return data_cleaned.upper()

    def is_valid(self):
        if not super().is_valid():
            return False
        try:
            academic_year = mdl.academic_year.find_academic_year_by_id(self.data.get('academic_year'))
        except ObjectDoesNotExist:
            return False
        learning_unit_years = mdl.learning_unit_year.find_gte_year_acronym(academic_year, self.data['acronym'])
        learning_unit_years_list = [learning_unit_year.acronym.lower() for learning_unit_year in learning_unit_years]
        if self.data['acronym'] in learning_unit_years_list:
            self.add_error('acronym', _('existing_acronym'))
        elif not re.match(self.acronym_regex, self.cleaned_data['acronym']):
            self.add_error('acronym', _('invalid_acronym'))
        elif self.cleaned_data["container_type"] == INTERNSHIP \
                and not (self.cleaned_data['internship_subtype']):
            self._errors['internship_subtype'] = _('field_is_required')
        else:
            return True

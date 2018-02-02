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
import re

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator, BaseValidator
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.business import learning_unit
from base.forms.bootstrap import BootstrapForm
from base.forms.utils.choice_field import add_blank
from base.models.campus import find_main_campuses
from base.models.entity_version import find_main_entities_version, find_main_entities_version_filtered_by_person
from base.models.enums import entity_container_year_link_type
from base.models.enums import learning_container_year_types
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES, INTERNSHIP
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY
from base.models.enums.learning_unit_management_sites import LearningUnitManagementSite
from base.models.enums.learning_unit_periodicity import PERIODICITY_TYPES
from base.models.enums.learning_unit_year_quadrimesters import LEARNING_UNIT_YEAR_QUADRIMESTERS
from base.models.learning_unit_year import MINIMUM_CREDITS, MAXIMUM_CREDITS
from reference.models.language import find_all_languages

MAX_RECORDS = 1000
READONLY_ATTR = "disabled"
PARTIM_FORM_READ_ONLY_FIELD = {'first_letter', 'acronym', 'common_title', 'common_title_english', 'requirement_entity',
                               'allocation_entity', 'language', 'periodicity', 'campus', 'academic_year',
                               'container_type', 'internship_subtype',
                               'additional_requirement_entity_1', 'additional_requirement_entity_2'}


def _create_first_letter_choices():
    return add_blank(LearningUnitManagementSite.choices())


def _create_learning_container_year_type_list():
    return add_blank(LEARNING_CONTAINER_YEAR_TYPES)


def create_faculty_learning_container_type_list():
    return add_blank(LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY)


class EntitiesVersionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.acronym


class MaxStrictlyValueValidator(BaseValidator):
    message = _('Ensure this value is less than %(limit_value)s.')
    code = 'max_strictly_value'

    def compare(self, a, b):
        return a >= b


class LearningUnitYearForm(BootstrapForm):
    acronym = forms.CharField(widget=forms.TextInput(attrs={'maxlength': "15", 'required': True}))
    academic_year = forms.ModelChoiceField(queryset=mdl.academic_year.find_academic_years(), required=True,
                                           empty_label=_('all_label'))
    status = forms.BooleanField(required=False, initial=True)
    internship_subtype = forms.ChoiceField(choices=add_blank(mdl.enums.internship_subtypes.INTERNSHIP_SUBTYPES),
                                           required=False)
    credits = forms.DecimalField(decimal_places=2, validators=[MinValueValidator(MINIMUM_CREDITS),
                                                               MaxValueValidator(MAXIMUM_CREDITS)])
    common_title = forms.CharField()
    common_title_english = forms.CharField(required=False, widget=forms.TextInput())
    partial_title = forms.CharField(required=False)
    partial_english_title = forms.CharField(required=False, widget=forms.TextInput())
    session = forms.ChoiceField(add_blank(mdl.enums.learning_unit_year_session.LEARNING_UNIT_YEAR_SESSION),
                                required=False)
    subtype = forms.CharField(widget=forms.HiddenInput())
    first_letter = forms.ChoiceField(choices=lazy(_create_first_letter_choices, tuple), required=True)
    container_type = forms.ChoiceField(choices=lazy(_create_learning_container_year_type_list, tuple),
                                       widget=forms.Select(attrs={'onchange': 'showInternshipSubtype()'}))
    faculty_remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    other_remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    periodicity = forms.CharField(widget=forms.Select(choices=PERIODICITY_TYPES))
    quadrimester = forms.CharField(widget=forms.Select(choices=add_blank(LEARNING_UNIT_YEAR_QUADRIMESTERS)),
                                   required=False)
    campus = forms.ModelChoiceField(queryset=find_main_campuses())
    requirement_entity = EntitiesVersionChoiceField(
        find_main_entities_version().none(),
        widget=forms.Select(
            attrs={
                'onchange': (
                    'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_1", false);'
                    'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2", true);'
                )
            }
        )
    )
    allocation_entity = EntitiesVersionChoiceField(queryset=find_main_entities_version(), required=True,
                                                   widget=forms.Select(attrs={'id': 'allocation_entity'}))
    additional_requirement_entity_1 = EntitiesVersionChoiceField(
        queryset=find_main_entities_version(),
        required=False,
        widget=forms.Select(
            attrs={
                'onchange':
                    'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2", false)',
                'disable': 'disable'
            }
        )
    )
    additional_requirement_entity_2 = EntitiesVersionChoiceField(queryset=find_main_entities_version(), required=False,
                                                                 widget=forms.Select(attrs={'disable': 'disable'}))
    language = forms.ModelChoiceField(find_all_languages(), empty_label=None)

    acronym_regex = "^[BLMW][A-Z]{2,4}\d{4}$"

    def clean_acronym(self):
        data_cleaned = self.data.get('first_letter', "") + self.cleaned_data.get('acronym')
        return data_cleaned.upper()

    def is_valid(self):
        if not super().is_valid():
            return False
        elif not re.match(self.acronym_regex, self.cleaned_data['acronym']):
            self.add_error('acronym', _('invalid_acronym'))
        elif self.cleaned_data["container_type"] == INTERNSHIP and not (self.cleaned_data['internship_subtype']):
            self.add_error('internship_subtype', _('field_is_required'))
        else:
            return True


class CreateLearningUnitYearForm(LearningUnitYearForm):

    def __init__(self, person, *args, **kwargs):
        super(CreateLearningUnitYearForm, self).__init__(*args, **kwargs)
        # When we create a learning unit, we can only select requirement entity which are attached to the person
        self.fields["requirement_entity"].queryset = find_main_entities_version_filtered_by_person(person)
        if person.user.groups.filter(name='faculty_managers').exists():
            self.fields["container_type"].choices = create_faculty_learning_container_type_list()
            del self.fields['internship_subtype']

    def is_valid(self):
        if not super().is_valid():
            return False
        academic_year_max = learning_unit.compute_max_academic_year_adjournment()
        learning_unit_years = mdl.learning_unit_year.find_gte_year_acronym(self.cleaned_data['academic_year'],
                                                                           self.cleaned_data['acronym'])
        learning_unit_years_list = [learning_unit_year.acronym for learning_unit_year in learning_unit_years]
        if self.cleaned_data['acronym'] in learning_unit_years_list:
            self.add_error('acronym', _('existing_acronym'))
            return False
        elif self.cleaned_data['academic_year'].year > academic_year_max:
            error_msg = _('learning_unit_creation_academic_year_max_error').format(academic_year_max)
            self._errors['academic_year'] = error_msg
            return False
        return True


class CreatePartimForm(CreateLearningUnitYearForm):
    partim_letter = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'text-center',
                                                                                 'style': 'text-transform: uppercase;',
                                                                                 'maxlength': "1",
                                                                                 'id': 'hdn_partim_letter',
                                                                                 'onchange': 'validate_acronym()'}))
    acronym_regex = "^[BLMW][A-Z]{2,4}\d{4}[A-Z]$"

    def __init__(self, learning_unit_year_parent, *args, **kwargs):
        self.learning_unit_year_parent = learning_unit_year_parent
        super(CreatePartimForm, self).__init__(*args, **kwargs)
        self.fields['container_type'].choices = _create_learning_container_year_type_list()
        # The credit of LUY partim cannot be greater than credit of full LUY
        self.fields['credits'].validators.append(MaxStrictlyValueValidator(learning_unit_year_parent.credits))
        self.set_read_only_fields()

    def set_read_only_fields(self):
        for field in PARTIM_FORM_READ_ONLY_FIELD:
            if self.fields.get(field):
                self.fields[field].widget.attrs[READONLY_ATTR] = READONLY_ATTR

    def clean_acronym(self):
        return super(CreatePartimForm, self).clean_acronym() + self.data.get('partim_letter', [])[0].upper()

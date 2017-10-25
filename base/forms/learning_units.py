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
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models import Prefetch
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.business.entity_version import SERVICE_COURSE
from base.business.learning_unit_year_with_context import append_latest_entities
from base.forms.common import get_clean_data, treat_empty_or_str_none_as_none
from base.models import entity_version as mdl_entity_version
from base.forms.bootstrap import BootstrapForm
from base.models.campus import find_administration_campuses
from base.models.entity_version import find_main_entities_version
from base.models.enums import entity_container_year_link_type
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES, INTERNSHIP
from base.models.enums.learning_unit_periodicity import PERIODICITY_TYPES
from base.models.learning_unit_year import check_if_acronym_regex_is_valid
from reference.models.language import find_all_languages

MIN_ACRONYM_LENGTH = 3

MAX_RECORDS = 1000
EMPTY_FIELD = "---------"


class LearningUnitYearForm(forms.Form):
    academic_year_id = forms.CharField(max_length=10, required=False)
    container_type = subtype = status = forms.CharField(required=False)
    acronym = title = requirement_entity_acronym = allocation_entity_acronym = forms.CharField(
        widget=forms.TextInput(attrs={'size': '10', 'class': 'form-control'}),
        max_length=20, required=False)
    with_entity_subordinated = forms.BooleanField(required=False)

    def clean_acronym(self):
        data_cleaned = self.cleaned_data.get('acronym')
        data_cleaned = treat_empty_or_str_none_as_none(data_cleaned)
        if data_cleaned and len(data_cleaned) < MIN_ACRONYM_LENGTH:
            raise ValidationError(_('LU_WARNING_INVALID_ACRONYM'))
        elif data_cleaned and len(data_cleaned) >= MIN_ACRONYM_LENGTH and check_if_acronym_regex_is_valid(
                data_cleaned) is None:
            raise ValidationError(_('LU_ERRORS_INVALID_REGEX_SYNTAX'))
        return data_cleaned

    def clean_academic_year_id(self):
        data_cleaned = self.cleaned_data.get('academic_year_id')
        if data_cleaned == '0':
            return None
        return data_cleaned

    def clean_requirement_entity_acronym(self):
        data_cleaned = self.cleaned_data.get('requirement_entity_acronym')
        if data_cleaned:
            return data_cleaned.upper()
        return data_cleaned

    def clean_allocation_entity_acronym(self):
        data_cleaned = self.cleaned_data.get('allocation_entity_acronym')
        if data_cleaned:
            return data_cleaned.upper()
        return data_cleaned

    def clean(self):
        return get_clean_data(self.cleaned_data)

    def get_activity_learning_units(self):
        return self.get_learning_units(False)

    def get_learning_units(self, service_course_search):
        clean_data = self.cleaned_data

        entity_version_prefetch = Prefetch('entity__entityversion_set',
                                           queryset=mdl_entity_version.search(),
                                           to_attr='entity_versions')

        entity_container_prefetch = Prefetch('learning_container_year__entitycontaineryear_set',
                                             queryset=mdl.entity_container_year.search(
                                                 link_type=[entity_container_year_link_type.ALLOCATION_ENTITY,
                                                            entity_container_year_link_type.REQUIREMENT_ENTITY])
                                             .prefetch_related(entity_version_prefetch),
                                             to_attr='entity_containers_year')

        clean_data['learning_container_year_id'] = _get_filter_learning_container_ids(clean_data)
        learning_units = mdl.learning_unit_year.search(**clean_data) \
                             .select_related('academic_year', 'learning_container_year',
                                             'learning_container_year__academic_year') \
                             .prefetch_related(entity_container_prefetch) \
                             .order_by('academic_year__year', 'acronym')[:MAX_RECORDS + 1]

        return [append_latest_entities(learning_unit, service_course_search) for learning_unit in
                learning_units]

    def get_service_course_learning_units(self):
        learning_units_service_course = self.get_learning_units(True)
        service_courses = []
        allocation_entity_acronym = self.cleaned_data['allocation_entity_acronym']
        requirement_entity_acronym = self.cleaned_data['requirement_entity_acronym']

        for learning_unit_service_course in learning_units_service_course:
            allocation_entity_service_course = learning_unit_service_course.entities. \
                get(entity_container_year_link_type.ALLOCATION_ENTITY)
            requirement_entity_service_course = learning_unit_service_course.entities. \
                get(entity_container_year_link_type.REQUIREMENT_ENTITY)

            if SERVICE_COURSE in learning_unit_service_course.entities and allocation_entity_service_course:
                if not requirement_entity_acronym:
                    if allocation_entity_acronym:
                        if allocation_entity_service_course.acronym == allocation_entity_acronym:
                            service_courses.append(learning_unit_service_course)
                elif requirement_entity_service_course.acronym == requirement_entity_acronym:
                    if not allocation_entity_acronym:
                        service_courses.append(learning_unit_service_course)
                    elif allocation_entity_service_course.acronym == allocation_entity_acronym:
                        service_courses.append(learning_unit_service_course)

        return service_courses


def _get_filter_learning_container_ids(filter_data):
    requirement_entity_acronym = filter_data.get('requirement_entity_acronym')
    allocation_entity_acronym = filter_data.get('allocation_entity_acronym')
    with_entity_subordinated = filter_data.get('with_entity_subordinated', False)
    entities_id_list = []
    if requirement_entity_acronym:
        entity_ids = _get_entities_ids(requirement_entity_acronym, with_entity_subordinated)
        entities_id_list += list(
            mdl.entity_container_year.search(link_type=entity_container_year_link_type.REQUIREMENT_ENTITY,
                                             entity_id=entity_ids)
                .values_list('learning_container_year', flat=True).distinct())
    if allocation_entity_acronym:
        entity_ids = _get_entities_ids(allocation_entity_acronym, False)
        entities_id_list += list(
            mdl.entity_container_year.search(link_type=entity_container_year_link_type.ALLOCATION_ENTITY,
                                             entity_id=entity_ids)
                .values_list('learning_container_year', flat=True).distinct())

    return entities_id_list if entities_id_list else None


def _get_entities_ids(requirement_entity_acronym, with_entity_subordinated):
    entities_ids = set()
    entity_versions = mdl.entity_version.search(acronym=requirement_entity_acronym)
    entities_ids |= set(entity_versions.values_list('entity', flat=True).distinct())

    if with_entity_subordinated:
        for entity_version in entity_versions:
            all_descendants = entity_version.find_descendants(entity_version.start_date)
            entities_ids |= {descendant.entity.id for descendant in all_descendants}
    return list(entities_ids)


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
    internship_subtype = forms.ChoiceField(choices=((None, "---------"),) +
                                                   mdl.enums.internship_subtypes.INTERNSHIP_SUBTYPES,
                                           required=False)
    credits = forms.CharField(widget=forms.TextInput(attrs={'required': True}))
    title = forms.CharField(widget=forms.TextInput(attrs={'required': True}))
    title_english = forms.CharField(required=False, widget=forms.TextInput())
    session = forms.ChoiceField(choices=((None, "---------"),) +
                                        mdl.enums.learning_unit_year_session.LEARNING_UNIT_YEAR_SESSION,
                                required=False)
    subtype = forms.CharField(widget=forms.HiddenInput())
    first_letter = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'text-center',
                                                                                 'maxlength': "1",
                                                                                 'readonly': 'readonly'}))
    learning_container_year_type = forms.ChoiceField(choices=lazy(create_learning_container_year_type_list, tuple),
                                                     widget=forms.Select(
                                                         attrs={'onchange': 'showInternshipSubtype(this.value)'}))

    faculty_remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    other_remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    periodicity = forms.CharField(widget=forms.Select(choices=PERIODICITY_TYPES))
    campus = forms.ModelChoiceField(queryset=find_administration_campuses(),
                                    widget=forms.Select(attrs={'onchange': 'setFirstLetter()'}))
    requirement_entity = EntitiesVersionChoiceField(find_main_entities_version(),
                                                    widget=forms.Select(attrs={
                                                        'onchange': 'showAdditionalEntity(this.value, "id_additional_entity_1")'}))

    allocation_entity = EntitiesVersionChoiceField(find_main_entities_version(),
                                                   required=False)
    additional_entity_1 = EntitiesVersionChoiceField(find_main_entities_version(),
                                                     required=False,
                                                     widget=forms.Select(attrs={
                                                         'onchange': 'showAdditionalEntity(this.value, "id_additional_entity_2")',
                                                         'disable': 'disable'}))
    additional_entity_2 = EntitiesVersionChoiceField(find_main_entities_version(),
                                                     required=False,
                                                     widget=forms.Select(attrs={'disable': 'disable'}))
    language = forms.ModelChoiceField(find_all_languages(), empty_label=None)

    acronym_regex = "^[LMNPWX][A-Z]{2,4}\d{4}$"

    class Meta:
        model = mdl.learning_unit_year.LearningUnitYear
        fields = ['learning_container_year_type', 'acronym', 'academic_year', 'status', 'internship_subtype',
                  'periodicity', 'credits', 'campus', 'title', 'title_english', 'additional_entity_1',
                  'additional_entity_2', 'allocation_entity', 'requirement_entity', 'subtype', 'language', 'session',
                  'faculty_remark', 'other_remark', ]

        widgets = {'acronym': forms.TextInput(attrs={'class': 'form-control form-acronym',
                                                     'id': 'acronym',
                                                     'maxlength': "15",
                                                     'required': True}),
                   'academic_year': forms.Select(attrs={'class': 'form-control',
                                                        'id': 'academic_year',
                                                        'required': True}),
                   'status': forms.CheckboxInput(attrs={'id': 'status'}),
                   'internship_subtype': forms.Select(attrs={'class': 'form-control',
                                                             'id': 'internship',
                                                             'disabled': 'disabled'}),
                   'credits': forms.TextInput(attrs={'class': 'form-control',
                                                     'id': 'credits',
                                                     'required': True}),
                   'title': forms.TextInput(attrs={'class': 'form-control',
                                                   'id': 'title',
                                                   'required': True}),
                   'title_english': forms.TextInput(attrs={'class': 'form-control',
                                                           'id': 'title_english',
                                                           'required': False}),
                   'session': forms.Select(attrs={'class': 'form-control',
                                                  'id': 'session',
                                                  'required': False}),
                   'subtype': forms.HiddenInput()
                   }

    def clean_acronym(self):
        data_cleaned = self.data.get('first_letter') + self.cleaned_data.get('acronym')
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
        elif self.cleaned_data['learning_container_year_type'] == INTERNSHIP \
                and not (self.cleaned_data['internship_subtype']):
            self._errors['internship_subtype'] = _('field_is_required')
        elif not self.cleaned_data['credits']:
            self._errors['credits'] = _('field_is_required')
            return False
        else:
            return True

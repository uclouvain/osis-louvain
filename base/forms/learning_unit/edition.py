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

from base.business.learning_unit import compute_max_academic_year_adjournment
from base.business.learning_units.edition import filter_biennial
from base.business.learning_units.perms import FACULTY_UPDATABLE_CONTAINER_TYPES
from base.forms.bootstrap import BootstrapForm
from base.forms.learning_unit_create import LearningUnitYearForm, PARTIM_FORM_READ_ONLY_FIELD
from base.forms.utils.choice_field import add_blank
from base.models import academic_year
from base.models.academic_year import AcademicYear
from base.models.enums.attribution_procedure import AttributionProcedures
from base.models.enums.entity_container_year_link_type import ENTITY_TYPE_LIST
from base.models.enums.learning_container_year_types import INTERNSHIP, DISSERTATION
from base.models.enums.learning_unit_periodicity import ANNUAL
from base.models.enums.learning_unit_year_subtypes import PARTIM
from base.models.enums.vacant_declaration_type import VacantDeclarationType

FULL_READ_ONLY_FIELDS = {"first_letter", "acronym", "academic_year", "container_type", "subtype"}
PARTIM_READ_ONLY_FIELDS = PARTIM_FORM_READ_ONLY_FIELD | {"is_vacant", "team", "type_declaration_vacant",
                                                         "attribution_procedure", "subtype"}
FACULTY_READ_ONLY_FIELDS = {"common_title", "common_title_english", "specific_title", "specific_title_english",
                            "faculty_remark", "other_remark", "campus", "status", "credits", "language",
                            "requirement_entity", "allocation_entity", "additional_requirement_entity_2", "is_vacant",
                            "type_declaration_vacant", "attribution_procedure", "subtype"}


class LearningUnitEndDateForm(BootstrapForm):
    academic_year = forms.ModelChoiceField(required=False,
                                           queryset=AcademicYear.objects.none(),
                                           empty_label=_('not_end_year'),
                                           label=_('academic_end_year')
                                           )

    def __init__(self, *args, **kwargs):
        self.learning_unit = kwargs.pop('learning_unit')
        super().__init__(*args, **kwargs)
        end_year = self.learning_unit.end_year

        self._set_initial_value(end_year)

        try:
            queryset = self._get_academic_years()

            periodicity = self.learning_unit.periodicity
            self.fields['academic_year'].queryset = filter_biennial(queryset, periodicity)
        except ValueError:
            self.fields['academic_year'].disabled = True

    def _set_initial_value(self, end_year):
        try:
            self.fields['academic_year'].initial = AcademicYear.objects.get(year=end_year)
        except (AcademicYear.DoesNotExist, AcademicYear.MultipleObjectsReturned):
            self.fields['academic_year'].initial = None

    def _get_academic_years(self):
        current_academic_year = academic_year.current_academic_year()
        min_year = current_academic_year.year
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


def _create_type_declaration_vacant_list():
    return add_blank(VacantDeclarationType.translation_choices())


def _create_attribution_procedure_list():
    return add_blank(AttributionProcedures.translation_choices())


class LearningUnitModificationForm(LearningUnitYearForm):
    is_vacant = forms.BooleanField(required=False)
    team = forms.BooleanField(required=False)
    type_declaration_vacant = forms.ChoiceField(required=False, choices=_create_type_declaration_vacant_list())
    attribution_procedure = forms.ChoiceField(required=False, choices=_create_attribution_procedure_list())

    def __init__(self, *args, person, learning_unit_year_instance=None, **kwargs):
        initial = kwargs.get("initial")
        learning_unit_year_subtype = initial.get("subtype") if initial else None
        learning_container_type = initial.get("container_type") if initial else None
        parent = learning_unit_year_instance.parent if learning_unit_year_instance else None

        self.learning_unit_end_date = kwargs.pop("end_date", None)

        super().__init__(*args, **kwargs)

        self.fields["requirement_entity"].queryset = person.find_main_entities_version

        self._disabled_fields_base_on_learning_unit_year_subtype(learning_unit_year_subtype)
        self._disabled_internship_subtype_field_if_not_internship_container_type(learning_container_type)

        if parent:
            self._set_status_value(parent)
            self._enabled_periodicity(parent)

        if person.is_faculty_manager():
            if initial.get("container_type") in FACULTY_UPDATABLE_CONTAINER_TYPES\
                    and learning_unit_year_subtype == "FULL":
                self._disabled_fields(FACULTY_READ_ONLY_FIELDS)

    def is_valid(self):
        if not BootstrapForm.is_valid(self):
            return False
        # Use a list of errors because when adding an error for a specific field with add_error, it is removed
        # from cleaned_data.
        errors_list = []
        if not self._is_requirement_entity_end_date_valid():
            errors_list.append(("requirement_entity",
                                _("requirement_entity_end_date_too_short")))
        if not self._are_requirement_and_allocation_entities_valid():
            errors_list.append(("allocation_entity",
                                _("requirement_and_allocation_entities_cannot_be_different")))
        self.add_errors(errors_list)
        return not self.errors

    def add_errors(self, list_errors):
        for field, error_msg in list_errors:
            self.add_error(field, error_msg)

    def _is_requirement_entity_end_date_valid(self):
        if self.cleaned_data["requirement_entity"].end_date is None:
            return True
        if self.learning_unit_end_date is None:
            return False
        return self.cleaned_data["requirement_entity"].end_date >= self.learning_unit_end_date

    def _are_requirement_and_allocation_entities_valid(self):
        return self._are_requirement_and_allocation_entities_the_same() or \
               self._can_requirement_and_allocation_entities_be_different()

    def _are_requirement_and_allocation_entities_the_same(self):
        return self.cleaned_data["requirement_entity"] == self.cleaned_data["allocation_entity"]

    def _can_requirement_and_allocation_entities_be_different(self):
        return self.cleaned_data["container_type"] not in [INTERNSHIP, DISSERTATION]

    def _disabled_fields_base_on_learning_unit_year_subtype(self, subtype):
        if subtype == PARTIM:
            self._disabled_fields(PARTIM_READ_ONLY_FIELDS)
        else:
            self._disabled_fields(FULL_READ_ONLY_FIELDS)

    def _disabled_internship_subtype_field_if_not_internship_container_type(self, container_type):
        if container_type != INTERNSHIP:
            self._disabled_fields(["internship_subtype"])

    def _disabled_fields(self, fields_to_disable):
        for field in fields_to_disable:
            self.fields[field].disabled = True

    def _set_status_value(self, parent):
        if parent.status is False:
            self.fields["status"].initial = parent.status
            self.fields["status"].disabled = True

    def _enabled_periodicity(self, parent):
        can_modify_periodicity = parent.learning_unit.periodicity == ANNUAL
        self.fields["periodicity"].disabled = not can_modify_periodicity

    def get_data_for_learning_unit(self):
        data_without_entities = {field: value for field, value in self.cleaned_data.items()
                                 if field.upper() not in ENTITY_TYPE_LIST}
        lu_data = {field: value for field, value in data_without_entities.items()
                   if field not in FULL_READ_ONLY_FIELDS}
        return lu_data

    def get_entities_data(self):
        return {entity_type.upper(): entity_version.entity if entity_version else None
                for entity_type, entity_version in self.cleaned_data.items()
                if entity_type.upper() in ENTITY_TYPE_LIST}

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
from abc import ABCMeta
from collections import OrderedDict

from django.db import transaction
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_unit.edition_volume import SimplifiedVolumeManagementForm
from base.forms.learning_unit.entity_form import EntityContainerBaseForm
from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm, LearningUnitYearModelForm, \
    LearningContainerModelForm, LearningContainerYearModelForm
from base.models import academic_year
from base.models.academic_year import MAX_ACADEMIC_YEAR_FACULTY, MAX_ACADEMIC_YEAR_CENTRAL, AcademicYear
from base.models.campus import Campus
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_year import LearningUnitYear
from reference.models import language
from base.models.enums.proposal_type import ProposalType

FULL_READ_ONLY_FIELDS = {"acronym", "academic_year", "container_type"}
FULL_PROPOSAL_READ_ONLY_FIELDS = {"academic_year", "container_type"}
PROPOSAL_READ_ONLY_FIELDS = {"container_type"}

FACULTY_OPEN_FIELDS = {
    'quadrimester',
    'session',
    'team',
    "faculty_remark",
    "other_remark",
    'common_title_english',
    'specific_title_english',
    "status",
    "professional_integration",
    "component-0-hourly_volume_partial_q1",
    "component-0-hourly_volume_partial_q2",
    "component-1-hourly_volume_partial_q1",
    "component-1-hourly_volume_partial_q2",
}

# This fields can not be disabled.
PROTECTED_FIELDS = {
    "component-0-id",
    "component-1-id",
}


class LearningUnitBaseForm(metaclass=ABCMeta):
    form_cls = form_cls_to_validate = [
        LearningUnitModelForm,
        LearningUnitYearModelForm,
        LearningContainerModelForm,
        LearningContainerYearModelForm,
        EntityContainerBaseForm,
        SimplifiedVolumeManagementForm
    ]

    forms = OrderedDict()
    data = {}
    subtype = None
    learning_unit_instance = None
    academic_year = None
    _warnings = None

    def __init__(self, instances_data, *args, **kwargs):
        self.forms = OrderedDict({cls: cls(*args, **instances_data[cls]) for cls in self.form_cls})

    def is_valid(self):
        if any([not form_instance.is_valid() for cls, form_instance in self.forms.items()
                if cls in self.form_cls_to_validate]):
            return False

        self.learning_unit_year_form.post_clean(self.learning_container_year_form.instance.container_type)
        self.learning_container_year_form.post_clean(self.learning_unit_year_form.cleaned_data["specific_title"])
        return not self.errors

    @transaction.atomic
    def save(self, commit=True):
        pass

    @cached_property
    def instance(self):
        if self.learning_unit_instance:
            return LearningUnitYear.objects.filter(
                academic_year=self.academic_year,
                learning_unit=self.learning_unit_instance,
                subtype=self.subtype
            ).get()
        return None

    @property
    def errors(self):
        return [form.errors for form in self.forms.values() if any(form.errors)]

    @property
    def fields(self):
        fields = OrderedDict()
        for cls, form_instance in self.forms.items():
            fields.update(form_instance.fields)
        return fields

    @property
    def cleaned_data(self):
        return [form.cleaned_data for form in self.forms.values()]

    @property
    def instances_data(self):
        data = {}
        for form_instance in self.forms.values():
            # For formset and container
            if hasattr(form_instance, 'instances_data'):
                data.update(form_instance.instances_data)
            else:
                columns = form_instance.fields.keys()
                data.update({col: getattr(form_instance.instance, col, None) for col in columns})
        return data

    @property
    def label_fields(self):
        """ Return a dictionary with the label of all fields """
        data = {}
        for form_instance in self.forms.values():
            data.update({
                key: field.label for key, field in form_instance.fields.items()
            })
        return data

    @property
    def changed_data(self):
        return [form.changed_data for form in self.forms.values()]

    def disable_fields(self, fields_to_disable):
        fields_to_disable -= PROTECTED_FIELDS
        for key, value in self.fields.items():
            if key in fields_to_disable:
                self._disable_field(value)

    @staticmethod
    def _disable_field(field):
        field.disabled = True
        field.required = False

    def get_context(self):
        return {
            'subtype': self.subtype,
            'learning_unit_form': self.learning_unit_form,
            'learning_unit_year_form': self.learning_unit_year_form,
            'learning_container_year_form': self.learning_container_year_form,
            'entity_container_form': self.entity_container_form,
            'simplified_volume_management_form': self.simplified_volume_management_form
        }

    def _validate_no_empty_title(self, common_title):
        specific_title = self.learning_unit_year_form.cleaned_data["specific_title"]
        if not common_title and not specific_title:
            self.learning_container_year_form.add_error(
                "common_title", _("You must either set the common title or the specific title"))
            return False
        return True

    @property
    def learning_container_form(self):
        return self.forms.get(LearningContainerModelForm)

    @property
    def learning_unit_form(self):
        return self.forms[LearningUnitModelForm]

    @property
    def learning_unit_year_form(self):
        return self.forms[LearningUnitYearModelForm]

    @property
    def learning_container_year_form(self):
        return self.forms[LearningContainerYearModelForm]

    @property
    def entity_container_form(self):
        return self.forms.get(EntityContainerBaseForm)

    @property
    def simplified_volume_management_form(self):
        return self.forms.get(SimplifiedVolumeManagementForm)

    def __iter__(self):
        """Yields the forms in the order they should be rendered"""
        return iter(self.forms.values())


class FullForm(LearningUnitBaseForm):
    subtype = learning_unit_year_subtypes.FULL

    def __init__(self, person, academic_year, learning_unit_instance=None, data=None, start_year=None, proposal=False,
                 postposal=None, proposal_type=None, *args, **kwargs):

        if not learning_unit_instance and not start_year:
            raise AttributeError("Should set at least learning_unit_instance or start_year instance.")
        self.academic_year = academic_year
        self.learning_unit_instance = learning_unit_instance
        self.person = person
        self.proposal = proposal
        self.data = data
        self.start_year = self.instance.learning_unit.start_year if self.instance else start_year
        self.proposal_type = proposal_type

        instances_data = self._build_instance_data(self.data, academic_year, proposal)
        super().__init__(instances_data, *args, **kwargs)
        if self.instance:
            self._disable_fields()
        else:
            self._restrict_academic_years_choice(postposal, proposal_type)

    def _restrict_academic_years_choice(self, postposal, proposal_type):
        if postposal:
            starting_academic_year = academic_year.starting_academic_year()
            end_year_range = MAX_ACADEMIC_YEAR_FACULTY if self.person.is_faculty_manager \
                else MAX_ACADEMIC_YEAR_CENTRAL

            self.fields["academic_year"].queryset = AcademicYear.objects.min_max_years(
                starting_academic_year.year, starting_academic_year.year + end_year_range
            )
        else:
            self._restrict_academic_years_choice_for_proposal_creation_suppression(proposal_type)

    def _disable_fields(self):
        if self.person.is_faculty_manager and not self.person.is_central_manager:
            self._disable_fields_as_faculty_manager()
        else:
            self._disable_fields_as_central_manager()

    def _disable_fields_as_faculty_manager(self):
        faculty_type_not_restricted = [t[0] for t in LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY]
        if self.proposal:
            self.disable_fields(PROPOSAL_READ_ONLY_FIELDS)
        elif self.instance.learning_container_year and \
                self.instance.learning_container_year.container_type not in faculty_type_not_restricted:
            self.disable_fields(self.fields.keys() - set(FACULTY_OPEN_FIELDS))
        else:
            self.disable_fields(FULL_READ_ONLY_FIELDS)

    def _disable_fields_as_central_manager(self):
        if self.proposal:
            self.disable_fields(FULL_PROPOSAL_READ_ONLY_FIELDS)
        else:
            self.disable_fields(FULL_READ_ONLY_FIELDS)

    def _build_instance_data(self, data, default_ac_year, proposal):
        return {
            LearningUnitModelForm: {
                'data': data,
                'instance': self.instance.learning_unit if self.instance else None,
            },
            LearningContainerModelForm: {
                'data': data,
                'instance': self.instance.learning_container_year.learning_container if self.instance else None,
            },
            LearningUnitYearModelForm: self._build_instance_data_learning_unit_year(data, default_ac_year),
            LearningContainerYearModelForm: self._build_instance_data_learning_container_year(data, proposal),
            EntityContainerBaseForm: {
                'data': data,
                'learning_container_year': self.instance.learning_container_year if self.instance else None,
                'person': self.person
            },
            SimplifiedVolumeManagementForm: {
                'data': data,
                'proposal': proposal,
                'queryset': LearningComponentYear.objects.filter(
                    learning_unit_year=self.instance
                ) if self.instance else LearningComponentYear.objects.none(),
                'person': self.person
            }

        }

    def _build_instance_data_learning_container_year(self, data, proposal):
        return {
            'data': data,
            'instance': self.instance.learning_container_year if self.instance else None,
            'proposal': proposal,
            'initial': {
                # Default campus selected 'Louvain-la-Neuve' if exist
                'campus': Campus.objects.filter(name='Louvain-la-Neuve').first()
            } if not self.instance else None,
            'person': self.person
        }

    def _build_instance_data_learning_unit_year(self, data, default_ac_year):
        return {
            'data': data,
            'instance': self.instance,
            'initial': {
                'status': True,
                'academic_year': default_ac_year,
                # Default language French
                'language': language.find_by_code('FR')
            } if not self.instance else None,
            'person': self.person,
            'subtype': self.subtype
        }

    def is_valid(self):
        result = super().is_valid()
        if result:
            result = self.entity_container_form.post_clean(
                self.learning_container_year_form.cleaned_data['container_type'],
                self.learning_unit_year_form.instance.academic_year)

        return result

    def save(self, commit=True):
        academic_year = self.academic_year

        learning_container = self.forms[LearningContainerModelForm].save(commit)
        learning_unit = self.learning_unit_form.save(
            start_year=self.start_year,
            learning_container=learning_container,
            commit=commit
        )
        container_year = self.learning_container_year_form.save(
            academic_year=academic_year,
            learning_container=learning_container,
            acronym=self.learning_unit_year_form.instance.acronym,
            commit=commit
        )

        # Save learning unit year (learning_component_year + entity_component_year)
        learning_unit_yr = self.learning_unit_year_form.save(
            learning_container_year=container_year,
            learning_unit=learning_unit,
            commit=commit
        )

        entity_container_years = self.entity_container_form.save(
            commit=commit,
            learning_container_year=learning_unit_yr.learning_container_year
        )

        self.simplified_volume_management_form.save_all_forms(
            learning_unit_yr,
            entity_container_years,
            commit=commit
        )

        return learning_unit_yr

    def _restrict_academic_years_choice_for_proposal_creation_suppression(self, proposal_type):
        if proposal_type in (ProposalType.CREATION.name, ProposalType.SUPPRESSION):
            if self.person.is_faculty_manager and proposal_type == ProposalType.CREATION.name:
                starting_academic_year = academic_year.current_academic_year().next()
            else:
                starting_academic_year = academic_year.starting_academic_year()

            end_year_range = MAX_ACADEMIC_YEAR_CENTRAL - 1 if self.person.is_faculty_manager \
                else MAX_ACADEMIC_YEAR_CENTRAL

            self.fields["academic_year"].queryset = academic_year.find_academic_years(
                start_year=starting_academic_year.year,
                end_year=starting_academic_year.year + end_year_range
            )

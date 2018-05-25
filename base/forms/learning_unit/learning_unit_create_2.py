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
from abc import ABCMeta
from collections import OrderedDict

from django.db import transaction
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from base.business.utils.model import merge_two_dicts
from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm, LearningUnitYearModelForm, \
    LearningContainerModelForm, LearningContainerYearModelForm, EntityContainerBaseForm
from base.forms.utils.acronym_field import split_acronym
from base.models import learning_unit_year
from base.models.campus import Campus
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_unit import LearningUnit
from reference.models import language

FULL_READ_ONLY_FIELDS = {"acronym", "academic_year", "container_type"}
FULL_PROPOSAL_READ_ONLY_FIELDS = {"academic_year", "container_type"}

PARTIM_FORM_READ_ONLY_FIELD = {'acronym_0', 'acronym_1', 'common_title', 'common_title_english',
                               'requirement_entity', 'allocation_entity', 'language', 'periodicity', 'campus',
                               'academic_year', 'container_type', 'internship_subtype',
                               'additional_requirement_entity_1', 'additional_requirement_entity_2'}

FACULTY_OPEN_FIELDS = {'quadrimester', 'session', 'team', "faculty_remark", "other_remark", 'common_title_english',
                       'specific_title_english', "status"}


class LearningUnitBaseForm(metaclass=ABCMeta):
    form_cls_to_validate = [
        LearningUnitModelForm,
        LearningUnitYearModelForm,
        LearningContainerModelForm,
        LearningContainerYearModelForm,
        EntityContainerBaseForm
    ]

    forms = OrderedDict()
    data = {}
    subtype = None
    learning_unit_instance = None
    academic_year = None
    _warnings = None

    def __init__(self, instances_data, *args, **kwargs):
        self.forms = OrderedDict({
            LearningContainerModelForm: LearningContainerModelForm(*args, **instances_data[LearningContainerModelForm]),
            LearningContainerYearModelForm: LearningContainerYearModelForm(*args, **instances_data[
                LearningContainerYearModelForm]),
            LearningUnitModelForm: LearningUnitModelForm(*args, **instances_data[LearningUnitModelForm]),
            LearningUnitYearModelForm: LearningUnitYearModelForm(*args, **instances_data[LearningUnitYearModelForm]),
            EntityContainerBaseForm: EntityContainerBaseForm(*args, **instances_data[EntityContainerBaseForm])
        })

    def is_valid(self):
        if any([not form_instance.is_valid() for cls, form_instance in self.forms.items()
                if cls in self.form_cls_to_validate]):
            return False

        self.learning_container_year_form.post_clean(self.learning_unit_year_form.cleaned_data["specific_title"])

        return not self.errors

    @transaction.atomic
    def save(self, commit=True):
        pass

    @cached_property
    def instance(self):
        if self.learning_unit_instance:
            return learning_unit_year.search(
                academic_year_id=self.academic_year.id,
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
            if isinstance(form_instance, EntityContainerBaseForm):
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
        for key, value in self.fields.items():
            if key in fields_to_disable:
                self._disable_field(value)

    def disable_all_fields_except(self, fields_not_to_disable):
        for key, value in self.fields.items():
            if key not in fields_not_to_disable:
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
            'entity_container_form': self.entity_container_form
        }

    def _validate_no_empty_title(self, common_title):
        specific_title = self.learning_unit_year_form.cleaned_data["specific_title"]
        if not common_title and not specific_title:
            self.learning_container_year_form.add_error(
                "common_title", _("must_set_common_title_or_specific_title"))
            return False
        return True

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
        return self.forms[EntityContainerBaseForm]

    def __iter__(self):
        """Yields the forms in the order they should be rendered"""
        return iter(self.forms.values())

    @property
    def warnings(self):
        if self._warnings is None:
            self._warnings = []
            for form in self.forms.values():
                if hasattr(form, 'warnings'):
                    self._warnings.extend(form.warnings)
        return self._warnings


class FullForm(LearningUnitBaseForm):

    subtype = learning_unit_year_subtypes.FULL

    def __init__(self, person, academic_year, learning_unit_instance=None, data=None, start_year=None, proposal=False,
                 *args, **kwargs):
        if not learning_unit_instance and not start_year:
            raise AttributeError("Should set at least learning_unit_instance or start_year instance.")
        self.academic_year = academic_year
        self.learning_unit_instance = learning_unit_instance
        self.person = person
        self.proposal = proposal
        self.data = data
        self.start_year = self.instance.learning_unit.start_year if self.instance else start_year

        instances_data = self._build_instance_data(self.data, academic_year, proposal)
        super().__init__(instances_data, *args, **kwargs)
        if self.instance:
            self._disable_fields()

    def _disable_fields(self):
        if self.person.is_faculty_manager():
            self._disable_fields_as_faculty_manager()
        else:
            self._disable_fields_as_central_manager()

    def _disable_fields_as_faculty_manager(self):
        if self.proposal:
            self.disable_fields(FACULTY_OPEN_FIELDS)
        else:
            self.disable_all_fields_except(FACULTY_OPEN_FIELDS)

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
            }
        }

    def _build_instance_data_learning_container_year(self, data, proposal):
        return {
            'data': data,
            'instance': self.instance.learning_container_year if self.instance else None,
            'proposal': proposal,
            'initial': {
                # Default campus selected 'Louvain-la-Neuve' if exist
                'campus': Campus.objects.filter(name='Louvain-la-Neuve').first(),
                # Default language French
                'language': language.find_by_code('FR')
            } if not self.instance else None,
            'person': self.person
        }

    def _build_instance_data_learning_unit_year(self, data, default_ac_year):
        return {
            'data': data,
            'instance': self.instance,
            'initial': {
                'status': True, 'academic_year': default_ac_year,
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
        learning_unit = self.forms[LearningUnitModelForm].save(
            start_year=self.start_year,
            learning_container=learning_container,
            commit=commit
        )
        container_year = self.forms[LearningContainerYearModelForm].save(
            academic_year=academic_year,
            learning_container=learning_container,
            acronym=self.forms[LearningUnitYearModelForm].instance.acronym,
            commit=commit
        )

        entity_container_years = self.entity_container_form.save(commit=commit, learning_container_year=container_year)

        # Save learning unit year (learning_unit_component +  learning_component_year + entity_component_year)
        learning_unit_year = self.forms[LearningUnitYearModelForm].save(
            learning_container_year=container_year,
            learning_unit=learning_unit,
            entity_container_years=entity_container_years,
            commit=commit
        )
        return learning_unit_year


def merge_data(data, inherit_lu_values):
    return merge_two_dicts(data.dict(), inherit_lu_values) if data else None


class PartimForm(LearningUnitBaseForm):
    subtype = learning_unit_year_subtypes.PARTIM
    form_cls_to_validate = [LearningUnitModelForm, LearningUnitYearModelForm]

    def __init__(self, person, learning_unit_full_instance, academic_year, learning_unit_instance=None,
                 data=None, *args, **kwargs):
        if not isinstance(learning_unit_full_instance, LearningUnit):
            raise AttributeError('learning_unit_full arg should be an instance of {}'.format(LearningUnit))
        if learning_unit_instance is not None and not isinstance(learning_unit_instance, LearningUnit):
            raise AttributeError('learning_unit_partim_instance arg should be an instance of {}'.format(LearningUnit))

        self.person = person
        self.academic_year = academic_year
        self.learning_unit_full_instance = learning_unit_full_instance
        self.learning_unit_instance = learning_unit_instance

        # Inherit values cannot be changed by user
        inherit_lu_values = self._get_inherit_learning_unit_full_value()
        inherit_luy_values = self._get_inherit_learning_unit_year_full_value()
        instances_data = self._build_instance_data(data, inherit_lu_values, inherit_luy_values)

        super(PartimForm, self).__init__(instances_data, *args, **kwargs)
        self.disable_fields(PARTIM_FORM_READ_ONLY_FIELD)

    @cached_property
    def learning_unit_year_full(self):
        return learning_unit_year.search(academic_year_id=self.academic_year.id,
                                         learning_unit=self.learning_unit_full_instance.id,
                                         subtype=learning_unit_year_subtypes.FULL).get()

    def _build_instance_data(self, data, inherit_lu_values, inherit_luy_values):
        return {
            LearningUnitModelForm: self._build_instance_data_learning_unit(data, inherit_lu_values),
            LearningUnitYearModelForm: self._build_instance_data_learning_unit_year(data, inherit_luy_values),
            # Cannot be modify by user [No DATA args provided]
            LearningContainerModelForm: {
                'instance': self.learning_unit_year_full.learning_container_year.learning_container,
            },
            LearningContainerYearModelForm: {
                'instance': self.learning_unit_year_full.learning_container_year,
                'person': self.person
            },
            EntityContainerBaseForm: {
                'learning_container_year': self.learning_unit_year_full.learning_container_year,
                'person': self.person
            }
        }

    def _build_instance_data_learning_unit_year(self, data, inherit_luy_values):
        return {
            'data': merge_data(data, inherit_luy_values),
            'instance': self.instance,
            'initial': self._get_initial_learning_unit_year_form() if not self.instance else None,
            'person': self.person,
            'subtype': self.subtype
        }

    def _build_instance_data_learning_unit(self, data, inherit_lu_values):
        return {
            'data': merge_data(data, inherit_lu_values),
            'instance': self.instance.learning_unit if self.instance else None,
            'initial': inherit_lu_values if not self.instance else None,
        }

    def _get_inherit_learning_unit_year_full_value(self):
        """This function will return the inherit value come from learning unit year FULL"""
        return {field: value for field, value in self._get_initial_learning_unit_year_form().items() if
                field in PARTIM_FORM_READ_ONLY_FIELD}

    def _get_initial_learning_unit_year_form(self):
        acronym = self.instance.acronym if self.instance else self.learning_unit_year_full.acronym
        initial_learning_unit_year = {
            'acronym': acronym,
            'academic_year': self.learning_unit_year_full.academic_year.id,
            'internship_subtype': self.learning_unit_year_full.internship_subtype,
            'attribution_procedure': self.learning_unit_year_full.attribution_procedure,
            'subtype': self.subtype,
            'credits': self.learning_unit_year_full.credits,
            'session': self.learning_unit_year_full.session,
            'quadrimester': self.learning_unit_year_full.quadrimester,
            'status': self.learning_unit_year_full.status,
            'specific_title': self.learning_unit_year_full.specific_title,
            'specific_title_english': self.learning_unit_year_full.specific_title_english
        }
        acronym_splited = split_acronym(acronym)
        initial_learning_unit_year.update({
            "acronym_{}".format(idx): acronym_part for idx, acronym_part in enumerate(acronym_splited)
        })
        return initial_learning_unit_year

    def _get_inherit_learning_unit_full_value(self):
        """This function will return the inherit value come from learning unit FULL"""
        return {
            'periodicity': self.learning_unit_full_instance.periodicity
        }

    def save(self, commit=True):
        start_year = self.instance.learning_unit.start_year if self.instance else \
                        self.learning_unit_full_instance.start_year

        # Save learning unit
        learning_unit = self.forms[LearningUnitModelForm].save(
            start_year=start_year,
            learning_container=self.learning_unit_year_full.learning_container_year.learning_container,
            commit=commit
        )

        # Get entity container form full learning container
        entity_container_years = self._get_entity_container_year()

        # Save learning unit year
        learning_unit_year = self.forms[LearningUnitYearModelForm].save(
            learning_container_year=self.learning_unit_year_full.learning_container_year,
            learning_unit=learning_unit,
            entity_container_years=entity_container_years,
            commit=commit
        )
        return learning_unit_year

    def _get_entity_container_year(self):
        return self.learning_unit_year_full.learning_container_year.entitycontaineryear_set.all()

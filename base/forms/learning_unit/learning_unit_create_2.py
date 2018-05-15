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
import abc
from abc import ABCMeta
from collections import OrderedDict

from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from base.business.learning_units import edition as edition_business
from base.business.utils.model import merge_two_dicts
from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm, LearningUnitYearModelForm, \
    LearningContainerModelForm, LearningContainerYearModelForm, EntityContainerBaseForm
from base.forms.utils.acronym_field import split_acronym
from base.models.academic_year import compute_max_academic_year_adjournment, AcademicYear
from base.models.campus import Campus
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_unit_year import LearningUnitYear
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

    form_classes = [
        LearningUnitModelForm,
        LearningUnitYearModelForm,
        LearningContainerModelForm,
        LearningContainerYearModelForm,
        EntityContainerBaseForm
    ]

    form_cls_to_validate = form_classes

    forms = OrderedDict()
    subtype = None
    _postponement = None
    instance = None
    _warnings = None

    def __init__(self, instances_data, *args, **kwargs):
        for form_class in self.form_classes:
            self.forms[form_class] = form_class(*args, **instances_data[form_class])

    def _is_update_action(self):
        return self.instance

    def is_valid(self):
        if any([not form_instance.is_valid() for cls, form_instance in self.forms.items()
                if cls in self.form_cls_to_validate]):
            return False

        self.learning_container_year_form.post_clean(self.learning_unit_year_form.cleaned_data["specific_title"])

        return not self.errors

    @transaction.atomic
    def save(self, commit=True, postponement=True):
        if self._is_update_action():
            return self._update_with_postponement(postponement)
        else:
            return self._create(commit, postponement)

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

    @staticmethod
    def _create_with_postponement(start_luy):
        new_luys = [start_luy]
        for ac_year in range(start_luy.learning_unit.start_year + 1, compute_max_academic_year_adjournment() + 1):
            new_luys.append(edition_business.duplicate_learning_unit_year(new_luys[0],
                                                                          AcademicYear.objects.get(year=ac_year)))
        return new_luys

    # TODO :: should reuse duplicate_learning_unit_year() function
    def _update_with_postponement(self, postponement=True):
        postponement = self._postponement or postponement

        entities_data = self.entity_container_form.get_linked_entities_forms()
        lu_type_full_data = self._get_flat_cleaned_data_apart_from_entities()
        edition_business.update_learning_unit_year_with_report(self.instance, lu_type_full_data,
                                                               entities_data,
                                                               with_report=postponement,
                                                               override_postponement_consistency=True)

    @abc.abstractmethod
    def _create(self, commit, postponement):
        pass

    def _get_flat_cleaned_data_apart_from_entities(self):
        all_clean_data = {}
        for cls, form_instance in self.forms.items():
            if cls in self.form_cls_to_validate and cls is not EntityContainerBaseForm:
                all_clean_data.update({field: value for field, value in form_instance.cleaned_data.items()
                                      if field not in FULL_READ_ONLY_FIELDS})
        return all_clean_data

    def make_postponement(self, learning_unit_year, postponement):
        if postponement:
            return self._create_with_postponement(learning_unit_year)
        return [learning_unit_year]

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

    def __init__(self, data, person, default_ac_year=None, instance=None, proposal=False, *args, **kwargs):
        check_learning_unit_year_instance(instance)
        self.instance = instance
        self.person = person
        self.proposal = proposal

        self.postponement = bool(int(data.get('postponement', 1))) if data else False

        self.academic_year = instance.academic_year if instance else default_ac_year
        instances_data = self._build_instance_data(data, default_ac_year, instance, proposal)
        super().__init__(instances_data, *args, **kwargs)

        if self._is_update_action():
            self._disable_fields()

        if not self.instance:
            self.fields['internship_subtype'].disabled = True

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

    def _build_instance_data(self, data, default_ac_year, instance, proposal):
        return{
            LearningUnitModelForm: {
                'data': data,
                'instance': instance.learning_unit if instance else None,
            },
            LearningContainerModelForm: {
                'data': data,
                'instance': instance.learning_container_year.learning_container if instance else None,
            },
            LearningUnitYearModelForm: self._build_instance_data_learning_unit_year(data, default_ac_year, instance),
            LearningContainerYearModelForm: self._build_instance_data_learning_container_year(data, instance, proposal),
            EntityContainerBaseForm: {
                'data': data,
                'learning_container_year': instance.learning_container_year if instance else None,
                'person': self.person
            }
        }

    def _build_instance_data_learning_container_year(self, data, instance, proposal):
        return {
            'data': data,
            'instance': instance.learning_container_year if instance else None,
            'proposal': proposal,
            'initial': {
                # Default campus selected 'Louvain-la-Neuve' if exist
                'campus': Campus.objects.filter(name='Louvain-la-Neuve').first(),
                # Default language French
                'language': language.find_by_code('FR')
            } if not instance else None,
            'person': self.person
        }

    def _build_instance_data_learning_unit_year(self, data, default_ac_year, instance):
        return {
            'data': data,
            'instance': instance,
            'initial': {
                'status': True, 'academic_year': default_ac_year,
            } if not instance else None,
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

    def _create(self, commit, postponement):
        academic_year = self.academic_year

        learning_container = self.forms[LearningContainerModelForm].save(commit)
        learning_unit = self.forms[LearningUnitModelForm].save(academic_year=academic_year,
                                                               learning_container=learning_container,
                                                               commit=commit)

        container_year = self.forms[LearningContainerYearModelForm].save(
            academic_year=academic_year,
            learning_container=learning_container,
            acronym=self.forms[LearningUnitYearModelForm].instance.acronym,
            commit=commit)

        entity_container_years = self.forms[EntityContainerBaseForm].save(
            learning_container_year=container_year,
            commit=commit)

        # Save learning unit year (learning_unit_component +  learning_component_year + entity_component_year)
        learning_unit_year = self.forms[LearningUnitYearModelForm].save(
            learning_container_year=container_year,
            learning_unit=learning_unit,
            entity_container_years=entity_container_years,
            commit=commit)

        return self.make_postponement(learning_unit_year, postponement)


def check_learning_unit_year_instance(instance):
    if instance and not isinstance(instance, LearningUnitYear):
        raise AttributeError('instance arg should be an instance of {}'.format(LearningUnitYear))


def merge_data(data, inherit_lu_values):
    return merge_two_dicts(data.dict(), inherit_lu_values) if data else None


class PartimForm(LearningUnitBaseForm):
    subtype = learning_unit_year_subtypes.PARTIM
    form_cls_to_validate = [LearningUnitModelForm, LearningUnitYearModelForm]

    def __init__(self, data, person, learning_unit_year_full, instance=None, *args, **kwargs):
        check_learning_unit_year_instance(instance)
        self.instance = instance
        self.person = person
        if not isinstance(learning_unit_year_full, LearningUnitYear):
            raise AttributeError('learning_unit_year_full arg should be an instance of {}'.format(LearningUnitYear))
        if learning_unit_year_full.subtype != learning_unit_year_subtypes.FULL:
            error_args = 'learning_unit_year_full arg should have a subtype {}'.format(learning_unit_year_subtypes.FULL)
            raise AttributeError(error_args)
        self.learning_unit_year_full = learning_unit_year_full

        # Inherit values cannot be changed by user
        inherit_lu_values = self._get_inherit_learning_unit_full_value()
        inherit_luy_values = self._get_inherit_learning_unit_year_full_value()
        instances_data = self._build_instance_data(data, inherit_lu_values, inherit_luy_values)

        super().__init__(instances_data, *args, **kwargs)
        self.disable_fields(self._get_fields_to_disabled())

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

    def _get_fields_to_disabled(self):
        field_to_disabled = PARTIM_FORM_READ_ONLY_FIELD.copy()
        return field_to_disabled

    def _get_inherit_learning_unit_year_full_value(self):
        """This function will return the inherit value come from learning unit year FULL"""
        return {field: value for field, value in self._get_initial_learning_unit_year_form().items() if
                field in self._get_fields_to_disabled()}

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
        learning_unit_full = self.learning_unit_year_full.learning_unit
        return {
            'periodicity': learning_unit_full.periodicity
        }

    def _create(self, commit, postponement):
        academic_year = self.learning_unit_year_full.academic_year

        # Save learning unit
        learning_unit = self.forms[LearningUnitModelForm].save(
            academic_year=academic_year,
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

        return self.make_postponement(learning_unit_year, postponement)

    def _get_entity_container_year(self):
        return self.learning_unit_year_full.learning_container_year.entitycontaineryear_set.all()

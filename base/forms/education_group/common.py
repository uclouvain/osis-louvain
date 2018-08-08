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
from django.core.validators import RegexValidator

from base.forms.learning_unit.entity_form import EntitiesVersionChoiceField
from base.models import campus, education_group_type, group_element_year
from base.models.campus import Campus
from base.models.education_group import EducationGroup
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import find_main_entities_version, get_last_version
from base.models.validation_rule import ValidationRule
from reference.models.language import Language


class MainTeachingCampusChoiceField(forms.ModelChoiceField):
    def __init__(self, queryset, *args, **kwargs):
        queryset = campus.find_main_campuses()
        super(MainTeachingCampusChoiceField, self).__init__(queryset, *args, **kwargs)


class MainEntitiesVersionChoiceField(EntitiesVersionChoiceField):
    def __init__(self, queryset, *args, **kwargs):
        queryset = find_main_entities_version()
        super(MainEntitiesVersionChoiceField, self).__init__(queryset, *args, **kwargs)


class ValidationRuleMixin:
    """
    Mixin for ModelForm

    It appends additional rules from VadilationRule table on fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rules = self.get_rules()
        self._set_rule_on_fields()

    def get_rules(self):
        result = {}
        for name, field in self.fields.items():
            full_name = self.field_reference(name)
            qs = ValidationRule.objects.filter(field_reference=full_name)
            if qs:
                result[name] = qs.get()
        return result

    def field_reference(self, name):
        return '.'.join([self._meta.model._meta.db_table, name])

    def _set_rule_on_fields(self):
        for name, field in self.fields.items():
            if name in self.rules:
                rule = self.rules[name]

                field.required = rule.required_field
                field.disabled = rule.disabled_field
                if not field.disabled:
                    field.initial = rule.initial_value

                field.validators.append(RegexValidator(rule.regex_rule, rule.regex_error_message or None))


class ValidationRuleEducationGroupTypeMixin(ValidationRuleMixin):
    """
    ValidationRuleMixin For EducationGroupType

    The object reference must be structured like that:
        {db_table_name}.{col_name}.{education_group_type_name}
    """

    def field_reference(self, name):
        return super().field_reference(name) + '.' + self.get_type()

    def get_type(self):
        if self.instance and self.instance.education_group_type:
            return self.instance.education_group_type.name
        elif "education_group_type" in self.initial:
            return self.initial["education_group_type"].name
        else:
            return ""


class EducationGroupYearModelForm(ValidationRuleEducationGroupTypeMixin, forms.ModelForm):
    category = None

    class Meta:
        model = EducationGroupYear
        field_classes = {
            "management_entity": MainEntitiesVersionChoiceField,
            "main_teaching_campus": MainTeachingCampusChoiceField
        }
        fields = []

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop("parent", None)

        if "initial" not in kwargs:
            kwargs["initial"] = {}

        # TODO use natural-key to select default value
        # Default campus selected 'Louvain-la-Neuve' if exist
        kwargs['initial']['main_teaching_campus'] = Campus.objects.filter(name='Louvain-la-Neuve').first()
        kwargs['initial']['enrollment_campus'] = Campus.objects.filter(name='Louvain-la-Neuve').first()
        kwargs['initial']['primary_language'] = Language.objects.filter(code='FR').first()

        super().__init__(*args, **kwargs)

        self._filter_education_group_type()
        self._init_and_disable_academic_year()
        self._preselect_entity_version_from_entity_value()

    def _filter_education_group_type(self):
        # In case of update, we need to fetch all parents
        if self.instance.pk:
            parents = EducationGroupYear.objects.filter(
                groupelementyear__child_branch=self.instance.pk
            )
        elif self.parent:
            parents = [self.parent]

        else:
            parents = []

        queryset = education_group_type.find_authorized_types(
            category=self.category,
            parents=parents
        )
        self.fields["education_group_type"].queryset = queryset

    def _init_and_disable_academic_year(self):
        if self.parent or self.instance.academic_year_id:
            academic_year = self.parent.academic_year if self.parent else self.instance.academic_year
            self.fields["academic_year"].initial = academic_year.id
            self.fields["academic_year"].disabled = True
            self.fields["academic_year"].required = False

    def _preselect_entity_version_from_entity_value(self):
        if getattr(self.instance, 'management_entity', None):
            self.initial['management_entity'] = get_last_version(self.instance.management_entity).pk


class EducationGroupModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO For the moment the start_year value is set after the validation
        self.fields["start_year"].required = False

    class Meta:
        model = EducationGroup
        fields = ("start_year", "end_year")

    def save(self, *args, start_year=None, **kwargs):
        if start_year:
            self.instance.start_year = start_year
        return super().save(*args, **kwargs)


class CommonBaseForm:
    forms = None

    def __init__(self, education_group_year_form, education_group_form):
        self.forms = {
            forms.ModelForm: education_group_year_form,
            EducationGroupModelForm: education_group_form
        }

    def is_valid(self):
        return all([form.is_valid() for form in self.forms.values()])

    def save(self):
        educ_group_year_form = self.forms[forms.ModelForm]
        educ_group_form = self.forms[EducationGroupModelForm]

        start_year = None
        if self._is_creation() and not educ_group_form.instance.start_year:
            start_year = educ_group_year_form.cleaned_data['academic_year'].year

        education_group = educ_group_form.save(start_year=start_year)
        educ_group_year_form.instance.education_group = education_group
        education_group_year = educ_group_year_form.save()
        self._save_group_element_year(educ_group_year_form.parent, education_group_year)
        return education_group_year

    def _is_creation(self):
        return not self.forms[EducationGroupModelForm].instance.id

    @staticmethod
    def _save_group_element_year(parent, child):
        # TODO :: what if this relation parent/child already exists? Should we create a new GroupElementYear anymore?
        if parent:
            group_element_year.get_or_create_group_element_year(parent, child_branch=child)

    @property
    def errors(self):
        errors = {}
        for form in self.forms.values():
            errors.update(form.errors)
        return errors

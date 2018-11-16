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
from django.conf import settings
from django.core.exceptions import PermissionDenied, ImproperlyConfigured, ValidationError
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from base.forms.common import ValidationRuleMixin
from base.forms.learning_unit.entity_form import EntitiesVersionChoiceField
from base.models import campus, group_element_year
from base.models.academic_calendar import AcademicCalendar
from base.models.campus import Campus
from base.models.education_group import EducationGroup
from base.models.education_group_type import find_authorized_types, EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import find_pedagogical_entities_version, get_last_version
from base.models.enums import academic_calendar_type, education_group_categories
from reference.models.language import Language
from rules_management.enums import TRAINING_PGRM_ENCODING_PERIOD, TRAINING_DAILY_MANAGEMENT, \
    MINI_TRAINING_PGRM_ENCODING_PERIOD, MINI_TRAINING_DAILY_MANAGEMENT, GROUP_PGRM_ENCODING_PERIOD, \
    GROUP_DAILY_MANAGEMENT
from rules_management.mixins import PermissionFieldMixin


class MainCampusChoiceField(forms.ModelChoiceField):
    def __init__(self, queryset, *args, **kwargs):
        queryset = campus.find_main_campuses()
        super().__init__(queryset, *args, **kwargs)


class MainEntitiesVersionChoiceField(EntitiesVersionChoiceField):
    def __init__(self, queryset, *args, **kwargs):
        queryset = find_pedagogical_entities_version()
        super(MainEntitiesVersionChoiceField, self).__init__(queryset, *args, **kwargs)


class EducationGroupTypeModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return _(obj.name)


class ValidationRuleEducationGroupTypeMixin(ValidationRuleMixin):
    """
    ValidationRuleMixin For EducationGroupType

    The object reference must be structured like that:
        {db_table_name}.{col_name}.{education_group_type_name}
    """

    def field_reference(self, name):
        return super().field_reference(name) + '.' + self.get_type()

    def get_type(self):
        # For creation
        if self.education_group_type:
            return self.education_group_type.external_id
        # For updating
        elif self.instance and self.instance.education_group_type:
            return self.instance.education_group_type.external_id
        return ""


class PermissionFieldEducationGroupMixin(PermissionFieldMixin):
    """
    Permission Field for educationgroup(year)

    This mixin will get allowed field on reference_field model according to perm's
    """
    def get_context(self):
        is_edition_period_egy_opened = AcademicCalendar.objects.open_calendars().filter(
            reference=academic_calendar_type.EDUCATION_GROUP_EDITION
        )
        if self.category == education_group_categories.TRAINING:
            return TRAINING_PGRM_ENCODING_PERIOD if is_edition_period_egy_opened else \
                TRAINING_DAILY_MANAGEMENT
        elif self.category == education_group_categories.MINI_TRAINING:
            return MINI_TRAINING_PGRM_ENCODING_PERIOD if is_edition_period_egy_opened else \
                MINI_TRAINING_DAILY_MANAGEMENT
        elif self.category == education_group_categories.GROUP:
            return GROUP_PGRM_ENCODING_PERIOD if is_edition_period_egy_opened else \
                GROUP_DAILY_MANAGEMENT
        return super().get_context()


class EducationGroupYearModelForm(ValidationRuleEducationGroupTypeMixin, PermissionFieldEducationGroupMixin,
                                  forms.ModelForm):
    category = None

    class Meta:
        model = EducationGroupYear
        field_classes = {
            "management_entity": MainEntitiesVersionChoiceField,
            "main_teaching_campus": MainCampusChoiceField,
            "enrollment_campus": MainCampusChoiceField,
            "education_group_type": EducationGroupTypeModelChoiceField,
        }
        fields = []
        widgets = {
            "duration": forms.NumberInput(attrs={'min': 1}),
            "min_constraint": forms.NumberInput(attrs={'min': 1}),
            "max_constraint": forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, education_group_type=None, user=None, **kwargs):
        self.user = user
        self.parent = kwargs.pop("parent", None)

        if not education_group_type and not kwargs.get('instance'):
            raise ImproperlyConfigured("Provide an education_group_type or an instance")

        self.education_group_type = education_group_type
        if self.education_group_type:
            if education_group_type not in find_authorized_types(self.category, self.parent):
                raise PermissionDenied("Unauthorized type {} for {}".format(education_group_type, self.category))

        super().__init__(*args, **kwargs)
        self._set_initial_values()
        self._filter_education_group_type()
        self._filter_management_entity_according_to_person()
        self._init_and_disable_academic_year()
        self._preselect_entity_version_from_entity_value()

    def _set_initial_values(self):
        default_campus = Campus.objects.filter(name='Louvain-la-Neuve').first()
        if 'main_teaching_campus' in self.fields:
            self.fields['main_teaching_campus'].initial = default_campus
        if 'enrollment_campus' in self.fields:
            self.fields['enrollment_campus'].initial = default_campus
        if 'primary_language' in self.fields:
            self.fields['primary_language'].initial = Language.objects.filter(code='FR').first()

        if self.parent and 'management_entity' in self.fields:
            self.fields['management_entity'].initial = self.parent.management_entity_version

    def _filter_education_group_type(self):
        # When the type is already given, we need to disabled the field
        if self.education_group_type:
            self.instance.education_group_type = self.education_group_type
            self._disable_field("education_group_type", self.education_group_type.pk)

        elif self.instance.pk:
            self._disable_field("education_group_type", self.instance.education_group_type.pk)

    def _init_and_disable_academic_year(self):
        if self.parent or self.instance.academic_year_id:
            academic_year = self.parent.academic_year if self.parent else self.instance.academic_year
            self._disable_field("academic_year", initial_value=academic_year.pk)

    def _preselect_entity_version_from_entity_value(self):
        if getattr(self.instance, 'management_entity', None):
            self.initial['management_entity'] = get_last_version(self.instance.management_entity).pk

    def _filter_management_entity_according_to_person(self):
        if 'management_entity' in self.fields:
            self.fields['management_entity'].queryset = \
                self.fields['management_entity'].queryset.filter(entity__in=self.user.person.linked_entities)

    def _disable_field(self, key, initial_value=None):
        field = self.fields[key]
        if initial_value:
            self.fields[key].initial = initial_value

        field.disabled = True
        field.required = False
        field.required = False

    def clean_acronym(self):
        data_cleaned = self.cleaned_data.get('acronym')
        if data_cleaned:
            return data_cleaned.upper()

    def clean_partial_acronym(self):
        data_cleaned = self.cleaned_data.get('partial_acronym')
        if data_cleaned:
            return data_cleaned.upper()


class EducationGroupModelForm(PermissionFieldEducationGroupMixin, forms.ModelForm):
    category = None

    class Meta:
        model = EducationGroup
        fields = ("start_year", "end_year")

    def save(self, *args, start_year=None, **kwargs):
        if start_year:
            self.instance.start_year = start_year
        return super().save(*args, **kwargs)


class CommonBaseForm:
    forms = None

    education_group_year_form_class = EducationGroupYearModelForm
    education_group_form_class = EducationGroupModelForm

    education_group_year_deleted = []

    def __init__(self, data, instance=None, parent=None, user=None, education_group_type=None, **kwargs):
        self.education_group_year_form = self.education_group_year_form_class(
            data,
            instance=instance,
            parent=parent,
            user=user,
            education_group_type=education_group_type,
            **kwargs
        )

        education_group = instance.education_group if instance else None
        self.education_group_form = self.education_group_form_class(
            data,
            user=user,
            instance=education_group,
        )

        self.forms = {
            forms.ModelForm: self.education_group_year_form,
            EducationGroupModelForm: self.education_group_form
        }

        start_year_field = self.education_group_form.fields["start_year"]

        if not (self._is_creation()):
            start_year_field.initial = self.education_group_form.instance.start_year
        else:
            start_year_field.widget = forms.HiddenInput(attrs={})

        start_year_field.disabled = True
        start_year_field.required = False

    def is_valid(self):
        result = all([form.is_valid() for form in self.forms.values()])
        if result:
            result = self._post_clean()
        return result

    def _post_clean(self):
        educ_group_form = self.education_group_form

        if self._is_creation() and not educ_group_form.instance.start_year:
            # Specific case, because start_date is hidden when creation, we should test start_date [validite] > end_date
            educ_group_form.instance.start_year = self.education_group_year_form.cleaned_data['academic_year'].year
            try:
                educ_group_form.instance.clean()
            except ValidationError as error:
                # Field is already contains in validation error
                educ_group_form.add_error(field=None, error=error)
                return False
        return True

    def save(self):
        start_year = None
        if self._is_creation() and not self.education_group_form.instance.start_year:
            start_year = self.education_group_year_form.cleaned_data['academic_year'].year

        education_group = self.education_group_form.save(start_year=start_year)
        self.education_group_year_form.instance.education_group = education_group
        education_group_year = self.education_group_year_form.save()
        self._save_group_element_year(self.education_group_year_form.parent, education_group_year)

        if hasattr(self, '_post_save'):
            post_save = self._post_save()
            self.education_group_year_deleted = post_save.get('object_list_deleted', [])

        return education_group_year

    def _is_creation(self):
        return not self.education_group_year_form.instance.id

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


class EducationGroupTypeForm(forms.Form):
    name = EducationGroupTypeModelChoiceField(
        EducationGroupType.objects.none(),
        label=_("Type of training"),
        required=True,
    )

    def __init__(self, parent, category, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].queryset = find_authorized_types(
            category=category,
            parents=parent
        )

        self.fields["name"].label = _("Which type of %(category)s do you want to create ?") % {"category": _(category)}


class SelectLanguage(forms.Form):
    language = forms.ChoiceField(widget=forms.RadioSelect,
                                 choices=settings.LANGUAGES,
                                 label=_('Select a language'),
                                 required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['language'] = translation.get_language()

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
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from base.models.enums.field_status import DISABLED, REQUIRED, ALERT, NOT_REQUIRED, FIXED
from base.models.validation_rule import ValidationRule

STEP_HALF_INTEGER = '0.5'


def get_clean_data(datas_to_clean):
    return {key: treat_empty_or_str_none_as_none(value) for (key, value) in datas_to_clean.items()}


def treat_empty_or_str_none_as_none(data):
    return None if not data or data == "NONE" else data


class TooManyResultsException(Exception):
    def __init__(self):
        super().__init__("Too many results returned.")


def set_trans_txt(form, texts_list):
    for trans_txt in texts_list:
        text_label = trans_txt.text_label.label
        text = trans_txt.text if trans_txt.text else ""
        setattr(form, text_label, mark_safe(text))


class WarningFormMixin:
    """
    Mixin for Form

    Add error if the field has warning at True and the user has not confirmed it.
    You must include confirmation_modal.html in the template
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confirmed = self.data.get("confirmed", False)

    def clean(self):
        cleaned_data = super().clean()

        for name, field in self.fields.items():
            if getattr(field, "warning", False):
                if not cleaned_data.get(name) and not self.confirmed:
                    self.add_warning(name, field)

        return cleaned_data

    def add_warning(self, name, field):
        self.add_error(name, _("This field is required."))
        field.widget.attrs['class'] = "has-warning"


class ValidationRuleMixin(WarningFormMixin):
    """
    Mixin for ModelForm

    It appends additional rules from VadilationRule table on fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rules = self.get_rules()
        self._set_rules_on_fields()

    def get_rules(self):
        result = {}

        for name, field in self.fields.items():
            qs = ValidationRule.objects.filter(field_reference=self.field_reference(name))
            if qs:
                result[name] = qs.get()

        return result

    def field_reference(self, name):
        return '.'.join([self._meta.model._meta.db_table, name])

    def _set_rules_on_fields(self):
        for name, field in self.fields.items():
            if name in self.rules:
                rule = self.rules[name]

                self.change_status(field, rule)

                field.initial = rule.initial_value

                field.validators.append(
                    RegexValidator(rule.regex_rule, rule.regex_error_message or None)
                )

    @staticmethod
    def change_status(field, rule):
        if rule.status_field in (DISABLED, FIXED):
            field.disabled = True
            field.required = False

        elif rule.status_field == REQUIRED:
            if not isinstance(field, forms.BooleanField):
                field.required = True

        elif rule.status_field == ALERT:
            field.warning = True

        elif rule.status_field == NOT_REQUIRED:
            field.required = False

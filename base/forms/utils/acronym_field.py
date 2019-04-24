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
import re

from django import forms
from django.utils.translation import ugettext_lazy as _

from base.forms.utils.choice_field import add_blank
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_unit_external_sites import LearningUnitExternalSite
from base.models.enums.learning_unit_management_sites import LearningUnitManagementSite


def _create_first_letter_choices():
    return add_blank(LearningUnitManagementSite.choices())


def _create_external_first_letter_choices():
    return add_blank(LearningUnitExternalSite.choices())


class AcronymInput(forms.MultiWidget):
    template_name = 'learning_unit/blocks/widget/acronym_widget.html'
    choices = _create_first_letter_choices()

    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs['class'] = 'text-uppercase'
        widgets = (
            forms.Select(attrs=attrs, choices=self.choices),
            forms.TextInput(attrs=attrs)
        )

        super().__init__(widgets)

    def decompress(self, value):
        if value:
            return [value[0], value[1:]]
        return ['', '']


class ExternalAcronymInput(AcronymInput):
    choices = _create_external_first_letter_choices()

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.widgets[0].attrs['required'] = True


class AcronymField(forms.MultiValueField):
    widget = AcronymInput

    def __init__(self, *args, **kwargs):
        max_length = kwargs.pop('max_length', None)
        list_fields = [
            forms.CharField(*args, max_length=1, **kwargs),
            forms.CharField(*args, max_length=max_length, **kwargs)
        ]
        super().__init__(list_fields, *args, **kwargs)
        self.label = _("Acronym")

    def compress(self, data_list):
        return ''.join(data_list).upper()


class ExternalAcronymField(AcronymField):
    widget = ExternalAcronymInput


class PartimAcronymInput(forms.MultiWidget):
    template_name = 'learning_unit/blocks/widget/partim_widget.html'

    def __init__(self, attrs=None):
        widgets = [
            forms.Select(choices=_create_first_letter_choices()),
            forms.TextInput(attrs={'class': 'text-uppercase'}),
            forms.TextInput(attrs={
                'class': 'text-center text-uppercase',
                'maxlength': "1",
                'onchange': 'validate_acronym()'
            })
        ]
        super().__init__(widgets)

    def decompress(self, value):
        if value:
            return split_acronym(value)
        return ['', '', '']


class PartimAcronymField(forms.MultiValueField):
    widget = PartimAcronymInput

    def __init__(self, *args, **kwargs):
        max_length = kwargs.pop('max_length', None)
        disabled = kwargs.pop('disabled', [True, True, False])

        list_fields = [
            forms.ChoiceField(choices=_create_first_letter_choices()),
            forms.CharField(max_length=max_length),
            forms.CharField(max_length=1)
        ]
        kwargs['require_all_fields'] = kwargs.pop('required', True)
        super().__init__(list_fields, *args, **kwargs)
        self.apply_attrs_to_widgets('disabled', disabled)
        self.label = _("Acronym")

    def apply_attrs_to_widgets(self, property, values):
        for index, subwidget in enumerate(self.widget.widgets):
            subwidget.attrs[property] = values[index]

    def compress(self, data_list):
        return ''.join(data_list).upper()


def split_acronym(value, subtype=learning_unit_year_subtypes.PARTIM, instance=None):
    """This function split acronym into small piece list
    Index 0 :  Localisation (L/M/...)
    Index 1 :  Sigle/Cnum
    Index 2 :  Subdivision
    """
    if subtype == learning_unit_year_subtypes.PARTIM:
        if instance and instance.pk:
            base_acronym = [value[0], value[1:-1], value[-1]]
        else:
            base_acronym = [value[0], value[1:]]
    else:
        last_digit_position = re.match('.+([0-9])[^0-9]*$', value).start(1)
        base_acronym = [value[0], value[1:last_digit_position + 1]]
    return base_acronym

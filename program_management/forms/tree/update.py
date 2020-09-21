# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from typing import Optional

from django import forms
from django.core.exceptions import ValidationError

import osis_common.ddd.interface
from base.forms.utils import choice_field
from base.models.enums.link_type import LinkTypes
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain.exception import RelativeCreditShouldBeGreaterOrEqualsThanZero
from program_management.ddd.service.write import update_link_service
from program_management.ddd.validators import _block_validator, _relative_credits


class UpdateLinkForm(forms.Form):
    access_condition = forms.BooleanField(required=False)
    is_mandatory = forms.BooleanField(required=False)
    block = forms.IntegerField(required=False, widget=forms.widgets.TextInput)
    link_type = forms.ChoiceField(choices=choice_field.add_blank(LinkTypes.choices()), required=False)
    comment = forms.CharField(widget=forms.widgets.Textarea, required=False)
    comment_english = forms.CharField(widget=forms.widgets.Textarea, required=False)
    relative_credits = forms.IntegerField(widget=forms.widgets.TextInput, required=False)

    def __init__(self, **kwargs):
        self.parent_node_code = kwargs.pop('parent_node_code')
        self.parent_node_year = kwargs.pop('parent_node_year')
        self.node_code = kwargs.pop('node_to_update_code')
        self.node_year = kwargs.pop('node_to_update_year')
        super().__init__(**kwargs)

    def clean_block(self):
        cleaned_block_type = self.cleaned_data.get('block', None)
        try:
            _block_validator.BlockValidator(cleaned_block_type).validate()
        except osis_common.ddd.interface.BusinessExceptions as business_exception:
            raise ValidationError(business_exception.messages)
        return cleaned_block_type

    def clean_relative_credits(self):
        cleaned_relative_credits = self.cleaned_data.get('relative_credits', None)
        try:
            _relative_credits.RelativeCreditsValidator(cleaned_relative_credits).validate()
        except RelativeCreditShouldBeGreaterOrEqualsThanZero as e:
            raise ValidationError(e.message)
        return cleaned_relative_credits

    def save(self) -> Optional['Link']:
        result = None
        if self.is_valid():
            result = update_link_service.update_link(self._create_update_command())
        return result

    def _create_update_command(self) -> command.UpdateLinkCommand:
        return command.UpdateLinkCommand(
            parent_node_code=self.parent_node_code,
            parent_node_year=self.parent_node_year,
            child_node_code=self.node_code,
            child_node_year=self.node_year,
            access_condition=self.cleaned_data.get("access_condition", False),
            is_mandatory=self.cleaned_data.get("is_mandatory", True),
            block=self.cleaned_data.get("block"),
            link_type=self.cleaned_data.get("link_type"),
            comment=self.cleaned_data.get("comment", ""),
            comment_english=self.cleaned_data.get("comment_english", ""),
            relative_credits=self.cleaned_data.get("relative_credits"),
        )

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
from typing import List, Type, Optional

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import BaseFormSet

import osis_common.ddd.interface
from base.ddd.utils import business_validator
from base.forms.utils import choice_field
from base.models.enums.link_type import LinkTypes
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import node
from program_management.ddd.repositories import load_node, load_authorized_relationship, node as node_repository
from program_management.ddd.service.write import paste_element_service
from program_management.ddd.validators import _block_validator
from program_management.models.enums.node_type import NodeType


class PasteNodesFormset(BaseFormSet):

    def get_form_kwargs(self, index):
        if self.form_kwargs:
            return self.form_kwargs[index]
        return {}

    @transaction.atomic
    def save(self) -> List[Optional['LinkIdentity']]:
        return [form.save() for form in self.forms]


def paste_form_factory(
        self,
        path_of_node_to_paste_into: str,
        node_to_paste_code: str,
        node_to_paste_year: int,
        **kwargs
) -> 'PasteNodeForm':
    form_class = _get_form_class(path_of_node_to_paste_into, node_to_paste_code, node_to_paste_year)
    return form_class(path_of_node_to_paste_into, node_to_paste_code, node_to_paste_year, **kwargs)


def _get_form_class(
        path_of_node_to_paste_into: str,
        node_to_paste_code: str,
        node_to_paste_year: int
) -> Type['PasteNodeForm']:
    node_to_paste_into_id = int(path_of_node_to_paste_into.split("|")[-1])
    node_to_paste_into = load_node.load(node_to_paste_into_id)

    node_identity = node.NodeIdentity(code=node_to_paste_code, year=node_to_paste_year)
    node_to_paste = node_repository.NodeRepository.get(node_identity)

    authorized_relationship = load_authorized_relationship.load()

    if node_to_paste_into.is_minor_major_list_choice():
        return PasteToMinorMajorListChoiceForm
    elif node_to_paste.node_type == NodeType.LEARNING_UNIT:
        return PasteLearningUnitForm
    elif node_to_paste_into.is_training() and node_to_paste.is_minor_major_list_choice():
        return PasteMinorMajorListChoiceToTrainingForm
    elif not authorized_relationship.is_authorized(node_to_paste_into.node_type, node_to_paste.node_type):
        return PasteNotAuthorizedChildren
    return PasteNodeForm


class PasteNodeForm(forms.Form):
    access_condition = forms.BooleanField(required=False)
    is_mandatory = forms.BooleanField(required=False)
    block = forms.IntegerField(required=False, widget=forms.widgets.TextInput)
    link_type = forms.ChoiceField(choices=choice_field.add_blank(LinkTypes.choices()), required=False)
    comment = forms.CharField(widget=forms.widgets.Textarea, required=False)
    comment_english = forms.CharField(widget=forms.widgets.Textarea, required=False)
    relative_credits = forms.IntegerField(widget=forms.widgets.TextInput, required=False)

    def __init__(
            self,
            to_path: str,
            node_to_paste_code: str,
            node_to_paste_year: int,
            path_to_detach: str = None,
            **kwargs
    ):
        self.to_path = to_path
        self.node_code = node_to_paste_code
        self.node_year = node_to_paste_year
        self.path_to_detach = path_to_detach
        super().__init__(**kwargs)

    def clean_block(self):
        cleaned_block_type = self.cleaned_data.get('block', None)
        try:
            _block_validator.BlockValidator(cleaned_block_type).validate()
        except osis_common.ddd.interface.BusinessExceptions as business_exception:
            raise ValidationError(business_exception.messages)
        return cleaned_block_type

    def save(self) -> Optional['LinkIdentity']:
        result = None
        if self.is_valid():
            try:
                result = paste_element_service.paste_element(self._create_paste_command())
            except osis_common.ddd.interface.BusinessExceptions as business_exception:
                self.add_error(None, business_exception.messages)
        return result

    def _create_paste_command(self) -> command.PasteElementCommand:
        return command.PasteElementCommand(
            node_to_paste_code=self.node_code,
            node_to_paste_year=self.node_year,
            path_where_to_paste=self.to_path,
            access_condition=self.cleaned_data.get("access_condition", False),
            is_mandatory=self.cleaned_data.get("is_mandatory", True),
            block=self.cleaned_data.get("block"),
            link_type=self.cleaned_data.get("link_type"),
            comment=self.cleaned_data.get("comment", ""),
            comment_english=self.cleaned_data.get("comment_english", ""),
            relative_credits=self.cleaned_data.get("relative_credits"),
            path_where_to_detach=self.path_to_detach
        )


class PasteLearningUnitForm(PasteNodeForm):
    access_condition = None
    link_type = None


class PasteMinorMajorListChoiceToTrainingForm(PasteNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._disable_all_but_block_fields()

    def _disable_all_but_block_fields(self):
        for field_name, field in self.fields.items():
            if field_name != "block":
                field.disabled = True


class PasteToMinorMajorListChoiceForm(PasteNodeForm):
    is_mandatory = None
    block = None
    link_type = None
    comment = None
    comment_english = None
    relative_credits = None

    def _create_paste_command(self) -> command.PasteElementCommand:
        return command.PasteElementCommand(
            node_to_paste_code=self.node_code,
            node_to_paste_year=self.node_year,
            path_where_to_paste=self.to_path,
            access_condition=self.cleaned_data.get("access_condition", False),
            is_mandatory=self.cleaned_data.get("is_mandatory", True),
            block=self.cleaned_data.get("block"),
            link_type=LinkTypes.REFERENCE,
            comment=self.cleaned_data.get("comment", ""),
            comment_english=self.cleaned_data.get("comment_english", ""),
            relative_credits=self.cleaned_data.get("relative_credits"),
            path_where_to_detach=self.path_to_detach
        )


class PasteNotAuthorizedChildren(PasteNodeForm):
    access_condition = None
    relative_credits = None

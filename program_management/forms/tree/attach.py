##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
import itertools
from typing import List, Type

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import BaseFormSet, BaseModelFormSet, modelformset_factory

import program_management.ddd.service.command
from base.ddd.utils import validation_message
from base.forms.utils import choice_field
from base.models import group_element_year
from base.models.authorized_relationship import AuthorizedRelationshipList
from base.models.enums import education_group_categories
from base.models.enums.link_type import LinkTypes
from base.models.group_element_year import GroupElementYear
from program_management.business.group_element_years.attach import AttachEducationGroupYearStrategy, \
    AttachLearningUnitYearStrategy
from program_management.business.group_element_years.management import CheckAuthorizedRelationshipAttach
from program_management.ddd.domain.node import Node
from program_management.ddd.repositories import load_node, load_authorized_relationship
from program_management.ddd.service import attach_node_service, command
from program_management.ddd.validators import _block_validator
from program_management.models.enums.node_type import NodeType


class AttachNodeFormSet(BaseFormSet):

    def get_form_kwargs(self, index):
        if self.form_kwargs:
            return self.form_kwargs[index]
        return {}

    @transaction.atomic
    def save(self) -> List[validation_message.BusinessValidationMessage]:
        return list(itertools.chain.from_iterable(
            [form.save() for form in self.forms]
        ))


def attach_form_factory(
        self,
        path_of_node_to_attach_from: str,
        node_to_attach_id: int,
        node_to_attach_type: NodeType,
        **kwargs
) -> 'AttachNodeForm':
    form_class = _get_form_class(path_of_node_to_attach_from, node_to_attach_id, node_to_attach_type)
    return form_class(path_of_node_to_attach_from, node_to_attach_id, node_to_attach_type, **kwargs)


def _get_form_class(
        path_of_node_to_attach_from: str,
        node_to_attach_id: int,
        node_to_attach_type: NodeType
) -> Type['AttachNodeForm']:
    node_to_attach_from_id = int(path_of_node_to_attach_from.split("|")[-1])
    node_to_attach_from = load_node.load_by_type(NodeType.EDUCATION_GROUP, node_to_attach_from_id)
    node_to_attach = load_node.load_by_type(node_to_attach_type, node_to_attach_id)
    authorized_relationship = load_authorized_relationship.load()

    if node_to_attach_from.is_minor_major_list_choice():
        return AttachToMinorMajorListChoiceForm
    elif node_to_attach.node_type == NodeType.LEARNING_UNIT:
        return AttachLearningUnitForm
    elif node_to_attach_from.is_training() and node_to_attach.is_minor_major_list_choice():
        return AttachMinorMajorListChoiceToTrainingForm
    elif not authorized_relationship.is_authorized(node_to_attach_from.node_type, node_to_attach.node_type):
        return AttachNotAuthorizedChildren
    return AttachNodeForm


class AttachNodeForm(forms.Form):
    access_condition = forms.BooleanField(required=False)
    is_mandatory = forms.BooleanField(required=False)
    block = forms.IntegerField(required=False, widget=forms.widgets.TextInput)
    link_type = forms.ChoiceField(choices=choice_field.add_blank(LinkTypes.choices()), required=False)
    comment = forms.CharField(widget=forms.widgets.Textarea, required=False)
    comment_english = forms.CharField(widget=forms.widgets.Textarea, required=False)
    relative_credits = forms.IntegerField(widget=forms.widgets.TextInput, required=False)

    def __init__(self, to_path: str, node_to_attach_id: int, node_to_attach_type: NodeType, **kwargs):
        self.to_path = to_path
        self.node_id = node_to_attach_id
        self.node_type = node_to_attach_type
        super().__init__(**kwargs)

    def clean_block(self):
        cleaned_block_type = self.cleaned_data.get('block', None)
        validator = _block_validator.BlockValidator(cleaned_block_type)
        if not validator.is_valid():
            raise ValidationError(validator.error_messages)
        return cleaned_block_type

    def save(self) -> List[validation_message.BusinessValidationMessage]:
        result = []
        if self.is_valid():
            result = attach_node_service.attach_node(self._get_attach_request())
            if result:
                self.add_error(None, result)
        return result

    def _get_attach_request(self) -> command.AttachNodeCommand:
        root_id = int(self.to_path.split("|")[0])
        return command.AttachNodeCommand(
            root_id=root_id,
            node_id_to_attach=self.node_id,
            type_of_node_to_attach=self.node_type,
            path_where_to_attach=self.to_path,
            commit=True,
            access_condition=self.cleaned_data.get("access_condition", False),
            is_mandatory=self.cleaned_data.get("is_mandatory", True),
            block=self.cleaned_data.get("block"),
            link_type=self.cleaned_data.get("link_type"),
            comment=self.cleaned_data.get("comment", ""),
            comment_english=self.cleaned_data.get("comment_english", ""),
            relative_credits=self.cleaned_data.get("relative_credits")
        )


class AttachLearningUnitForm(AttachNodeForm):
    access_condition = None
    link_type = None


class AttachMinorMajorListChoiceToTrainingForm(AttachNodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._disable_all_but_block_fields()

    def _disable_all_but_block_fields(self):
        for field_name, field in self.fields.items():
            if field_name != "block":
                field.disabled = True


class AttachToMinorMajorListChoiceForm(AttachNodeForm):
    is_mandatory = None
    block = None
    link_type = None
    comment = None
    comment_english = None
    relative_credits = None

    def _get_attach_request(self) -> command.AttachNodeCommand:
        attach_request = super()._get_attach_request()
        return attach_request._replace(link_type=LinkTypes.REFERENCE.name)


class AttachNotAuthorizedChildren(AttachNodeForm):
    access_condition = None
    relative_credits = None


class GroupElementYearForm(forms.ModelForm):
    class Meta:
        model = GroupElementYear
        fields = [
            "relative_credits",
            "is_mandatory",
            "block",
            "link_type",
            "comment",
            "comment_english",
            "access_condition"
        ]
        widgets = {
            "comment": forms.Textarea(attrs={'rows': 5}),
            "comment_english": forms.Textarea(attrs={'rows': 5}),
            "block": forms.TextInput(),
            "relative_credits": forms.TextInput(attrs={'style': 'min-width: 40px;'})
        }

    def __init__(self, *args, parent=None, child_branch=None, child_leaf=None, **kwargs):
        super().__init__(*args, **kwargs)
        # No need to attach FK to an existing GroupElementYear
        if not self.instance.pk:
            self.instance.parent = parent
            self.instance.child_leaf = child_leaf
            self.instance.child_branch = child_branch
            self.initial['relative_credits'] = int(self.instance.child.credits) \
                if self.instance.child and self.instance.child.credits else None

        if self.instance.parent:
            self._define_fields()

    def _define_fields(self):
        if self.instance.child_branch and not self._check_authorized_relationship(
                self.instance.child_branch.education_group_type):
            self.fields.pop("access_condition")

        elif self._is_education_group_year_a_minor_major_option_list_choice(self.instance.parent) and \
                not self._is_education_group_year_a_minor_major_option_list_choice(self.instance.child_branch):
            self._keep_only_fields(["access_condition"])

        elif self.instance.parent.education_group_type.category == education_group_categories.TRAINING and \
                self._is_education_group_year_a_minor_major_option_list_choice(self.instance.child_branch):
            self._disable_all_fields(["block"])

        elif self.instance.child_leaf:
            self.fields.pop("link_type")
            self.fields.pop("access_condition")

        else:
            self.fields.pop("relative_credits")
            self.fields.pop("access_condition")

    def save(self, commit=True):
        return super().save(commit)

    def clean_link_type(self):
        """
        All of these controls only work with child branch.
        The validation with learning_units (child_leaf) is in the model.
        """
        data_cleaned = self.cleaned_data.get('link_type')
        if not self.instance.child_branch:
            return data_cleaned

        link = GroupElementYear(pk=self.instance.pk, child_branch=self.instance.child_branch, link_type=data_cleaned)
        check = CheckAuthorizedRelationshipAttach(
            self.instance.parent,
            link_to_attach=link,
        )
        if not check.is_valid():
            raise ValidationError(check.errors)
        return data_cleaned

    def clean(self):
        strategy = AttachEducationGroupYearStrategy if self.instance.child_branch else \
            AttachLearningUnitYearStrategy
        strategy(parent=self.instance.parent, child=self.instance.child, instance=self.instance).is_valid()
        return super().clean()

    def _check_authorized_relationship(self, child_type):
        return self.instance.parent.education_group_type.authorized_parent_type.filter(child_type=child_type).exists()

    def _disable_all_fields(self, fields_to_not_disable):
        for name, field in self.fields.items():
            if name not in fields_to_not_disable:
                field.disabled = True

    def _keep_only_fields(self, fields_to_keep):
        self.fields = {name: field for name, field in self.fields.items() if name in fields_to_keep}

    @staticmethod
    def _is_education_group_year_a_minor_major_option_list_choice(egy):
        return egy.is_minor_major_option_list_choice if egy else False


class BaseGroupElementYearFormset(BaseModelFormSet):
    def changed_forms(self):
        return [f for f in self if f.has_changed()]

    def save(self, commit=True):
        for f in self:
            f.save()

    def get_form_kwargs(self, index):
        if self.form_kwargs:
            return self.form_kwargs[index]
        return {}


GroupElementYearFormset = modelformset_factory(
    model=GroupElementYear,
    form=GroupElementYearForm,
    formset=BaseGroupElementYearFormset,
    extra=0,
)

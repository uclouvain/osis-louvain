##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Tuple

from django import forms
from django.forms import formset_factory, BaseFormSet

import program_management.ddd.domain.exception
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.forms.exceptions import InvalidFormException
from base.forms.utils import choice_field
from base.forms.utils.fields import OsisRichTextFormField
from base.models.enums.education_group_types import TrainingType
from base.models.enums.link_type import LinkTypes
from infrastructure.messages_bus import message_bus_instance
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception


class LinkForm(forms.Form):
    relative_credits = forms.IntegerField(required=False)
    is_mandatory = forms.BooleanField(required=False)
    access_condition = forms.BooleanField(required=False)
    link_type = forms.ChoiceField(choices=choice_field.add_blank(LinkTypes.choices()), required=False)
    block = forms.IntegerField(required=False)
    comment_fr = OsisRichTextFormField(config_name='comment_link_only', required=False)
    comment_en = OsisRichTextFormField(config_name='comment_link_only', required=False)

    def __init__(self, *args, parent_obj: 'Node', child_obj: 'Node', **kwargs):
        self.parent_obj = parent_obj
        self.child_obj = child_obj
        super().__init__(*args, **kwargs)

        self.__initialize_fields()

    def __initialize_fields(self):
        if self.is_a_parent_minor_major_option_list_choice():
            fields_to_exclude = (
                'relative_credits',
                'is_mandatory',
                'link_type',
                'block',
                'comment_fr',
                'comment_en',
            )
        elif self.is_a_child_minor_major_option_list_choice() and \
                self.parent_obj.node_type.name in TrainingType.get_names():
            fields_to_exclude = (
                'relative_credits',
                'is_mandatory',
                'link_type',
                'access_condition',
                'comment_fr',
                'comment_en',
            )
        elif self.is_a_link_with_child_of_learning_unit():
            fields_to_exclude = (
                'link_type',
                'access_condition',
            )
        else:
            fields_to_exclude = (
                'relative_credits',
                'access_condition',
            )
        [self.fields.pop(field_name) for field_name in fields_to_exclude]

    def is_a_link_with_child_of_learning_unit(self):
        return self.child_obj.is_learning_unit()

    def is_a_parent_minor_major_option_list_choice(self):
        return self.parent_obj and self.parent_obj.is_minor_major_option_list_choice()

    def is_a_child_minor_major_option_list_choice(self):
        return self.child_obj.is_minor_major_option_list_choice()

    def generate_update_link_command(self) -> 'command.UpdateLinkCommand':
        return command.UpdateLinkCommand(
            child_node_code=self.child_obj.code,
            child_node_year=self.child_obj.year,
            access_condition=self.cleaned_data.get('access_condition', False),
            is_mandatory=self.cleaned_data.get('is_mandatory', False),
            block=self.cleaned_data.get('block'),
            link_type=self.cleaned_data.get('link_type'),
            comment=self.cleaned_data.get('comment_fr'),
            comment_english=self.cleaned_data.get('comment_en'),
            relative_credits=self.cleaned_data.get('relative_credits'),
            parent_node_code=self.parent_obj.code,
            parent_node_year=self.parent_obj.year
        )

    def handle_save_exception(
            self,
            business_exceptions: 'MultipleBusinessExceptions'
    ):
        for e in business_exceptions.exceptions:
            if isinstance(e, exception.ReferenceLinkNotAllowedException) or \
                    isinstance(e, exception.ChildTypeNotAuthorizedException) or\
                    isinstance(e, exception.MaximumChildTypesReachedException) or \
                    isinstance(e, exception.MinimumChildTypesNotRespectedException):
                self.add_error("link_type", e.message)
            elif isinstance(e, exception.InvalidBlockException):
                self.add_error("block", e.message)
            elif isinstance(e, exception.RelativeCreditShouldBeLowerOrEqualThan999) or \
                    isinstance(e, exception.RelativeCreditShouldBeGreaterOrEqualsThanZero):
                self.add_error("relative_credits", e.message)


class BaseContentFormSet(BaseFormSet):

    def get_form_kwargs(self, index):
        if self.form_kwargs:
            return self.form_kwargs[index]
        return {}

    def save(self) -> Tuple[command.BulkUpdateLinkCommand, List['Link']]:
        if self.is_valid():
            try:
                cmd = self.generate_bulk_update_link_command()
                updated_links = message_bus_instance.invoke(cmd)
                return cmd, updated_links
            except program_management.ddd.domain.exception.BulkUpdateLinkException as e:
                for form in self.forms:
                    if e.exceptions.get(form.generate_update_link_command()):
                        form.handle_save_exception(e.exceptions[form.generate_update_link_command()])

        raise InvalidFormException()

    def generate_bulk_update_link_command(self) -> 'command.BulkUpdateLinkCommand':
        changed_forms = [form for form in self.forms if form.has_changed()]
        update_link_commands = [form.generate_update_link_command() for form in changed_forms]

        bulk_command = command.BulkUpdateLinkCommand(
            working_tree_year=self.forms[0].parent_obj.year,
            working_tree_code=self.forms[0].parent_obj.code,
            update_link_cmds=update_link_commands
        )
        return bulk_command


ContentFormSet = formset_factory(form=LinkForm, formset=BaseContentFormSet, extra=0)

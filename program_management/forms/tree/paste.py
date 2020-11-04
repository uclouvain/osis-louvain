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
from typing import List, Optional

from django.db import transaction
from django.forms import BaseFormSet

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.forms.exceptions import InvalidFormException
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception
from program_management.ddd.service.write import paste_element_service
from program_management.forms.content import LinkForm


class PasteNodeForm(LinkForm):
    def __init__(self, *args, path_to_detach: str, **kwargs):
        self.path_to_detach = path_to_detach
        super().__init__(*args, **kwargs)

    def generate_paste_command(self) -> command.PasteElementCommand:
        return command.PasteElementCommand(
            node_to_paste_code=self.child_obj.code,
            node_to_paste_year=self.child_obj.year,
            path_where_to_paste=str(self.parent_obj.node_id),
            access_condition=self.cleaned_data.get("access_condition", False),
            is_mandatory=self.cleaned_data.get("is_mandatory", True),
            block=self.cleaned_data.get("block"),
            link_type=self.cleaned_data.get("link_type"),
            comment=self.cleaned_data.get("comment_fr", ""),
            comment_english=self.cleaned_data.get("comment_en", ""),
            relative_credits=self.cleaned_data.get("relative_credits"),
            path_where_to_detach=self.path_to_detach,
        )

    def save(self):
        if self.is_valid():
            try:
                return paste_element_service.paste_element(self.generate_paste_command())
            except MultipleBusinessExceptions as e:
                self.handle_save_exception(e)
        raise InvalidFormException()

    def handle_save_exception(self, business_exceptions: 'MultipleBusinessExceptions'):
        for e in business_exceptions.exceptions:
            if isinstance(e, exception.ReferenceLinkNotAllowedException) or \
                    isinstance(e, exception.ReferenceLinkNotAllowedWithLearningUnitException) or\
                    isinstance(e, exception.ChildTypeNotAuthorizedException) or \
                    isinstance(e, exception.MaximumChildTypesReachedException):
                self.add_error("link_type", e.message)
            elif isinstance(e, exception.InvalidBlockException):
                self.add_error("block", e.message)
            elif isinstance(e, exception.RelativeCreditShouldBeLowerOrEqualThan999) or \
                    isinstance(e, exception.RelativeCreditShouldBeGreaterOrEqualsThanZero):
                self.add_error("relative_credits", e.message)
            else:
                self.add_error("", e.message)


class BasePasteNodesFormset(BaseFormSet):
    def get_form_kwargs(self, index):
        if self.form_kwargs:
            return self.form_kwargs[index]
        return {}

    @transaction.atomic
    def save(self) -> List[Optional['LinkIdentity']]:
        results = []
        is_a_form_invalid = False
        for form in self.forms:
            try:
                results.append(form.save())
            except InvalidFormException:
                is_a_form_invalid = True

        if is_a_form_invalid:
            raise InvalidFormException()

        return results

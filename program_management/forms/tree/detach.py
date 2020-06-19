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
from django import forms
from django.core.exceptions import ValidationError

import osis_common.ddd.interface
from base.ddd.utils import business_validator
from program_management.ddd import command
from program_management.ddd.domain import link
from program_management.ddd.service.write import detach_node_service
from program_management.ddd.validators import _path_validator


class DetachNodeForm(forms.Form):
    path = forms.CharField(widget=forms.HiddenInput, required=True)

    def clean_path(self):
        cleaned_path = self.cleaned_data.get("path")
        try:
            _path_validator.PathValidator(cleaned_path).validate()
        except osis_common.ddd.interface.BusinessExceptions as business_exception:
            raise ValidationError(business_exception.messages)
        return cleaned_path

    def save(self) -> link.LinkIdentity:
        detach_node_command = command.DetachNodeCommand(path_where_to_detach=self.cleaned_data["path"], commit=True)
        return detach_node_service.detach_node(detach_node_command)

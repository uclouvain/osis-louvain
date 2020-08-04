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
from django.utils.translation import gettext_lazy as _

from base.forms.utils import choice_field
from base.models.enums.education_group_categories import Categories
from program_management.ddd import command
from program_management.ddd.service.read import allowed_children_types_service


class SelectTypeForm(forms.Form):
    name = forms.ChoiceField(required=True)

    def __init__(self, category, path_to=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["name"].label = _("Which type of %(category)s do you want to create ?") % {
            "category": Categories[category].value
        }
        self._init_name_choice(category, path_to)

    def _init_name_choice(self, category, path_to):
        cmd = command.GetAllowedChildTypeCommand(category=category, path_to_paste=path_to)
        allowed_child_types = allowed_children_types_service.get_allowed_child_types(cmd)
        self.fields["name"].choices = sorted(
            tuple((allowed_type.name, allowed_type.value) for allowed_type in allowed_child_types),
            key=lambda type: type[1]
        )
        self.fields["name"].choices = choice_field.add_blank(self.fields["name"].choices)

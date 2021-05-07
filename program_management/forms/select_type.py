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
from typing import Set

from django import forms
from django.utils.translation import gettext_lazy as _

from base.forms.utils import choice_field
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import EducationGroupTypesEnum
from education_group.auth.roles.central_manager import CentralManager
from program_management.ddd import command
from program_management.ddd.service.read import allowed_children_types_service


class SelectTypeForm(forms.Form):
    name = forms.ChoiceField(required=True)

    def __init__(self, person, category, path_to=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["name"].label = _("Which type of %(category)s do you want to create ?") % {
            "category": Categories[category].value
        }
        self.fields["name"].choices = self.get_name_choices(person, category, path_to)

    @staticmethod
    def get_name_choices(person, category, path_to):
        cmd = command.GetAllowedChildTypeCommand(category=category, path_to_paste=path_to)
        allowed_child_types = allowed_children_types_service.get_allowed_child_types(cmd)
        allowed_child_types = _filter_according_role_scope(person, allowed_child_types)
        choices = sorted(
            tuple((allowed_type.name, allowed_type.value) for allowed_type in allowed_child_types),
            key=lambda type: type[1]
        )
        return choice_field.add_blank(choices)


# TODO: Move permission/role logic to DDD
def _filter_according_role_scope(person: 'Person', education_group_types: Set[EducationGroupTypesEnum]):
    role_rows = CentralManager.objects.filter(person=person)
    if role_rows:
        allowed_types_according_scope = set(itertools.chain.from_iterable(
            role_row.get_allowed_education_group_types() for role_row in role_rows
        ))
        education_group_types = filter(lambda type: type.name in allowed_types_according_scope, education_group_types)
    return education_group_types

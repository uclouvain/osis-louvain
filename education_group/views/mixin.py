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
from base.models.enums.education_group_types import GroupType
from base.utils.cache import ElementCache
from education_group.ddd import command as command_education_group
from education_group.ddd.domain.exception import GroupNotFoundException
from education_group.ddd.service.read import get_group_service
from education_group.templatetags.academic_year_display import display_as_academic_year
from program_management.ddd import command as command_program_management
from program_management.ddd.service.read import element_selected_service
from django.utils.translation import gettext_lazy as _

from program_management.ddd.service.read import get_program_tree_version_from_node_service


class ElementSelectedClipBoardMixin:
    def get_selected_element_clipboard_message(self) -> str:
        return ElementSelectedClipBoardSerializer(self.request).get_selected_element_clipboard_message()


class ElementSelectedClipBoardSerializer:
    def __init__(self, request):
        self.request = request

    def get_selected_element_clipboard_message(self):
        element_selected = element_selected_service.retrieve_element_selected(self.request.user.id)
        if not element_selected:
            return ""
        return "<strong>{clipboard_title}</strong><br>{object_str}".format(
            clipboard_title=_("Cut element") if element_selected["action"] == ElementCache.ElementCacheAction.CUT.value
            else _("Copied element"),
            object_str=self._get_element_selected_str(element_selected)
        )

    def _get_element_selected_str(self, element_selected) -> str:
        try:
            return self._get_group_str(element_selected)
        except GroupNotFoundException:
            return "{} - {}".format(
                element_selected["element_code"],
                display_as_academic_year(element_selected["element_year"])
            )

    def _get_group_str(self, element_selected) -> str:
        group = get_group_service.get_group(
            command_education_group.GetGroupCommand(
                code=element_selected["element_code"],
                year=element_selected["element_year"]
            )
        )
        element_selected_str = "{} - {}".format(group.code, group.abbreviated_title)

        if group.type.name not in GroupType.get_names():
            version = get_program_tree_version_from_node_service.get_program_tree_version_from_node(
                command_program_management.GetProgramTreeVersionFromNodeCommand(
                    code=element_selected["element_code"],
                    year=element_selected["element_year"]
                )
            )
            if not version.is_standard:
                element_selected_str += "[{}]".format(version.version_name)

        element_selected_str += " - {}".format(group.academic_year)
        return element_selected_str

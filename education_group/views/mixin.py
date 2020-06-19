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
from base.utils.cache import ElementCache
from program_management.ddd.service.read import element_selected_service
from django.utils.translation import gettext_lazy as _


class ElementSelectedClipBoardMixin:
    def get_selected_element_clipboard_message(self) -> str:
        element_selected = element_selected_service.retrieve_element_selected(self.request.user.id)
        if not element_selected:
            return ""
        return "<strong>{clipboard_title}</strong><br>{object_str}".format(
            clipboard_title=_("Cut element") if element_selected["action"] == ElementCache.ElementCacheAction.CUT
            else _("Copied element"),
            object_str="{} - {}".format(element_selected["element_code"], element_selected["element_year"])
        )

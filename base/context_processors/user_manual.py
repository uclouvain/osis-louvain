##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import collections

UserManual = collections.namedtuple("UserManual", "name, url, contextual_paths")

UNDEFINED_VIEW_NAME = "UNDEFINED"

GLOBAL = UserManual(
    name="global",
    url="https://uclouvain.be/fare",
    contextual_paths=[]
)

EDUCATIONAL_INFORMATION = UserManual(
    name="educational_information",
    url="http://uclouvain.github.io/osis/assets/educational_information_manual_fr.pdf",
    contextual_paths=["learning_units_summary", "learning_unit_pedagogy"]
)

TUTOR_EDUCATIONAL_INFORMATION = UserManual(
    name="tutor_educational_information",
    url="http://uclouvain.github.io/osis/assets/tutor_educational_information_manual_fr.pdf",
    contextual_paths=["list_my_attributions_summary_editable", "view_educational_information"]
)

MANUALS = [
    GLOBAL,
    EDUCATIONAL_INFORMATION,
    TUTOR_EDUCATIONAL_INFORMATION
]


def user_manual_url(request):
    view_name = request.resolver_match.url_name if request.resolver_match else UNDEFINED_VIEW_NAME
    contextual_manual = find_contextual_user_manual(view_name, MANUALS, GLOBAL)

    manual_urls = {manual.name: manual.url for manual in MANUALS}
    manual_urls.update(contextual=contextual_manual.url)

    return {"user_manual": manual_urls}


def find_contextual_user_manual(view_name, manuals, default_manual):
    contextual_manual = next(
        (manual for manual in manuals if view_name in manual.contextual_paths),
        default_manual
    )
    return contextual_manual

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
from django import forms


def set_remote_validation(
        field: forms.Field,
        url: str,
        validate_if_empty: bool = False,
        validate_on_load: bool = False) -> None:
    parameters = {
        "data-parsley-remote": url,
        "data-parsley-remote-validator": "async-osis",
        "data-parsley-trigger": "focusin focusout input load",
    }
    if validate_if_empty:
        parameters["data-parsley-validate-if-empty"] = True
    if validate_on_load:
        parameters["data-parsley-group"] = "validateOnLoad"

    field.widget.attrs.update(
        parameters
    )

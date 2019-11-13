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
from django.utils.translation import gettext_lazy as _
from openpyxl.utils import get_column_letter

from base import models as mdl_base


def get_name_or_username(a_user):
    person = mdl_base.person.find_by_user(a_user)
    return "{}, {}".format(person.last_name, person.first_name) if person else a_user.username


def convert_boolean(a_boolean_value):
    return _('yes') if a_boolean_value else _('no')


def _get_all_columns_reference(nb_columns):
    letters = []
    nb_col = 1
    while nb_col < nb_columns+1:
        letters.append(get_column_letter(nb_col))
        nb_col += 1
    return letters

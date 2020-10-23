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
from education_group.models.group_year import GroupYear


def generate_node_code(code_from_standard_root_node: str, year: int) -> str:
    last_partial_acronym = _get_last_partial_acronym_using(code_from_standard_root_node, year).partial_acronym
    return last_partial_acronym[:-4] + str(int(last_partial_acronym[-4:][:-1]) + 1) + last_partial_acronym[-1:]


def _get_last_partial_acronym_using(code: str, year: int) -> bool:
    return GroupYear.objects.filter(
        partial_acronym__startswith=code[:-4],
        partial_acronym__endswith=code[-1:],
        academic_year__year=year
    ).order_by("partial_acronym").last()

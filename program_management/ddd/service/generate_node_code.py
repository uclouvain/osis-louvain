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
from program_management.ddd.repositories.check_node_code_exists import check_node_code_exists


def generate_node_code(code_from_standard_root_node: str, year: int) -> str:
    counter = 1
    new_partial_acronym = code_from_standard_root_node
    while check_node_code_exists(code_from_standard_root_node, year):
        incrementation = str(int(code_from_standard_root_node[-4:][:-1]) + counter)
        new_partial_acronym = code_from_standard_root_node[:-4] + incrementation + code_from_standard_root_node[-1:]
        counter += 1
    return new_partial_acronym

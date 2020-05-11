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
from osis_common.ddd import interface


class FillInProgramTreeContentCommand(interface.CommandRequest):
    def __init__(
            self,
            from_root_node_code: str,
            from_root_node_year: int,
            to_root_node_code: str,
            to_root_node_year: int
    ):
        self.from_root_node_code = from_root_node_code
        self.from_root_node_year = from_root_node_year
        self.to_root_node_code = to_root_node_code
        self.to_root_node_year = to_root_node_year

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
from typing import Optional

from osis_common.ddd import interface


class GetGroupCommand(interface.CommandRequest):
    def __init__(self, code: str, year: int):
        self.code = code
        self.year = year


class CreateOrphanGroupCommand(interface.CommandRequest):
    def __init__(
            self,
            code: str,
            year: int,
            type: str,
            abbreviated_title: str,
            title_fr: str,
            title_en: str,
            credits: int,
            constraint_type: str,
            min_constraint: int,
            max_constraint: int,
            management_entity_acronym: str,
            teaching_campus_name: str,
            organization_name: str,
            remark_fr: str,
            remark_en: str,
            start_year: int,
            end_year: Optional[int] = None
    ):
        self.code = code
        self.year = year
        self.type = type
        self.abbreviated_title = abbreviated_title
        self.title_fr = title_fr
        self.title_en = title_en
        self.credits = credits
        self.constraint_type = constraint_type
        self.min_constraint = min_constraint
        self.max_constraint = max_constraint
        self.management_entity_acronym = management_entity_acronym
        self.teaching_campus_name = teaching_campus_name
        self.organization_name = organization_name
        self.remark_fr = remark_fr
        self.remark_en = remark_en
        self.start_year = start_year
        self.end_year = end_year


class CopyGroupCommand(interface.CommandRequest):
    def __init__(self, from_code: str, from_year: int, to_year: int):
        self.from_code = from_code
        self.from_year = from_year
        self.to_year = to_year

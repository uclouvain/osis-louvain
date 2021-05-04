##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from decimal import Decimal

import attr

from osis_common.ddd.interface import DTO


@attr.s(frozen=True, slots=True)
class ApplicantFromRepositoryDTO(DTO):
    first_name = attr.ib(type=str)
    last_name = attr.ib(type=str)
    global_id = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class VacantCourseFromRepositoryDTO(DTO):
    code = attr.ib(type=str)
    year = attr.ib(type=int)
    title = attr.ib(type=str)
    is_in_team = attr.ib(type=bool)
    entity_allocation = attr.ib(type=str)
    vacant_declaration_type = attr.ib(type=str)
    lecturing_volume_available = attr.ib(type=Decimal)
    practical_volume_available = attr.ib(type=Decimal)


@attr.s(frozen=True, slots=True)
class ApplicationFromRepositoryDTO(DTO):
    uuid = attr.ib(type=str)
    applicant_global_id = attr.ib(type=str)
    vacant_course_code = attr.ib(type=str)
    vacant_course_year = attr.ib(type=int)
    lecturing_volume = attr.ib(type=Decimal)
    practical_volume = attr.ib(type=Decimal)
    remark = attr.ib(type=str)
    course_summary = attr.ib(type=str)

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

from ddd.logic.application.domain.model.entity_allocation import EntityAllocation
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYearIdentity
from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class VacantCourseIdentity(interface.EntityIdentity):
    academic_year = attr.ib(type=AcademicYearIdentity)
    code = attr.ib(type=str)

    def __str__(self):
        return "{} - ({})".format(self.code, self.academic_year)

    @property
    def year(self) -> int:
        return self.academic_year.year


@attr.s(slots=True, hash=False, eq=False)
class VacantCourse(interface.RootEntity):
    entity_id = attr.ib(type=VacantCourseIdentity)
    lecturing_volume_available = attr.ib(type=Decimal)
    practical_volume_available = attr.ib(type=Decimal)
    title = attr.ib(type=str)
    vacant_declaration_type = attr.ib(type=str)
    is_in_team = attr.ib(type=bool)
    entity_allocation = attr.ib(type=EntityAllocation)

    @property
    def year(self) -> int:
        return self.entity_id.year

    @property
    def code(self) -> str:
        return self.entity_id.code

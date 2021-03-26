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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from base.models import academic_year
from osis_common.ddd import interface
from program_management.ddd.domain.academic_year import AcademicYear


class GetAcademicYear(interface.DomainService):
    @classmethod
    def get_next_academic_year(cls) -> 'AcademicYear':
        year = academic_year.current_academic_year().year + 1
        return AcademicYear(year)

    @classmethod
    def get_current_academic_year(cls) -> 'AcademicYear':
        year = academic_year.current_academic_year().year
        return AcademicYear(year)

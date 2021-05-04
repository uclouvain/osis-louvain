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
from typing import Union

from ddd.logic.application.commands import ApplyOnVacantCourseCommand
from ddd.logic.application.domain.model.vacant_course import VacantCourseIdentity
from ddd.logic.application.dtos import VacantCourseFromRepositoryDTO
from ddd.logic.shared_kernel.academic_year.builder.academic_year_identity_builder import AcademicYearIdentityBuilder
from osis_common.ddd.interface import EntityIdentityBuilder


class VacantCourseIdentityBuilder(EntityIdentityBuilder):

    @classmethod
    def build_from_repository_dto(cls, dto_object: VacantCourseFromRepositoryDTO) -> VacantCourseIdentity:
        academic_year_identity = AcademicYearIdentityBuilder.build_from_year(dto_object.year)
        return VacantCourseIdentity(code=dto_object.code, academic_year=academic_year_identity)

    @classmethod
    def build_from_command(cls, cmd: Union[ApplyOnVacantCourseCommand]) -> VacantCourseIdentity:
        academic_year_identity = AcademicYearIdentityBuilder.build_from_year(cmd.academic_year)
        return VacantCourseIdentity(code=cmd.code, academic_year=academic_year_identity)

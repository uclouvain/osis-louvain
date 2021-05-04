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
from ddd.logic.application.domain.builder.vacant_course_identity_builder import VacantCourseIdentityBuilder
from ddd.logic.application.domain.model.entity_allocation import EntityAllocation
from ddd.logic.application.domain.model.vacant_course import VacantCourse
from ddd.logic.application.dtos import VacantCourseFromRepositoryDTO
from osis_common.ddd.interface import RootEntityBuilder


class VacantCourseBuilder(RootEntityBuilder):
    @classmethod
    def build_from_repository_dto(
            cls,
            dto: VacantCourseFromRepositoryDTO,
    ) -> VacantCourse:
        return VacantCourse(
            entity_id=VacantCourseIdentityBuilder.build_from_repository_dto(dto),
            title=dto.title,
            is_in_team=dto.is_in_team,
            vacant_declaration_type=dto.vacant_declaration_type,
            entity_allocation=EntityAllocation(dto.entity_allocation),
            lecturing_volume_available=dto.lecturing_volume_available,
            practical_volume_available=dto.practical_volume_available,
        )

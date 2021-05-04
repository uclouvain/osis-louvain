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
import uuid
from typing import List

from ddd.logic.application.commands import ApplyOnVacantCourseCommand
from ddd.logic.application.domain.model.applicant import Applicant, ApplicantIdentity
from ddd.logic.application.domain.model.application import Application, ApplicationIdentity
from ddd.logic.application.domain.model.vacant_course import VacantCourse, VacantCourseIdentity
from ddd.logic.application.domain.validator.validators_by_business_action import ApplyOnVacantCourseValidatorList
from ddd.logic.application.dtos import ApplicationFromRepositoryDTO
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYearIdentity
from osis_common.ddd.interface import RootEntityBuilder


class ApplicationBuilder(RootEntityBuilder):
    @classmethod
    def build_from_command(
            cls,
            applicant: Applicant,
            vacant_course: VacantCourse,
            cmd: ApplyOnVacantCourseCommand,
            all_existing_applications: List[Application]
    ) -> 'RootEntity':
        ApplyOnVacantCourseValidatorList(
            command=cmd,
            applicant=applicant,
            vacant_course=vacant_course,
            all_existing_applications=all_existing_applications
        ).validate()

        return Application(
            entity_id=ApplicationIdentity(uuid=uuid.uuid4()),
            applicant_id=applicant.entity_id,
            course_id=vacant_course.entity_id,
            lecturing_volume=cmd.lecturing_volume,
            practical_volume=cmd.practical_volume,
            course_summary=cmd.course_summary,
            remark=cmd.remark
        )

    @classmethod
    def build_from_repository_dto(
            cls,
            dto: ApplicationFromRepositoryDTO,
    ) -> Application:
        vacant_course_academic_year_id = AcademicYearIdentity(year=dto.vacant_course_year)
        return Application(
            entity_id=ApplicationIdentity(uuid=dto.uuid),
            applicant_id=ApplicantIdentity(global_id=dto.applicant_global_id),
            course_id=VacantCourseIdentity(code=dto.vacant_course_code, academic_year=vacant_course_academic_year_id),
            lecturing_volume=dto.lecturing_volume,
            practical_volume=dto.practical_volume,
            course_summary=dto.course_summary,
            remark=dto.remark
        )

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
from django.db import transaction

from ddd.logic.application.commands import ApplyOnVacantCourseCommand
from ddd.logic.application.domain.builder.application_builder import ApplicationBuilder
from ddd.logic.application.domain.model.applicant import ApplicantIdentity
from ddd.logic.application.domain.model.application import ApplicationIdentity
from ddd.logic.application.domain.model.vacant_course import VacantCourseIdentity
from ddd.logic.application.repository.i_applicant_respository import IApplicantRepository
from ddd.logic.application.repository.i_application_repository import IApplicationRepository
from ddd.logic.application.repository.i_vacant_course_repository import IVacantCourseRepository


@transaction.atomic()
def apply_on_vacant_course(
        cmd: ApplyOnVacantCourseCommand,
        application_repository: IApplicationRepository,
        applicant_repository: IApplicantRepository,
        vacant_course_repository: IVacantCourseRepository,
) -> ApplicationIdentity:
    # GIVEN
    applicant = applicant_repository.get(entity_id=ApplicantIdentity(cmd.global_id))
    vacant_course = vacant_course_repository.get(
        entity_id=VacantCourseIdentity(code=cmd.code, academic_year=cmd.academic_year)
    )
    all_existing_applications = application_repository.search(global_id=cmd.global_id)

    # WHEN
    application = ApplicationBuilder.build_from_command(applicant, vacant_course, cmd, all_existing_applications)

    # THEN
    application_repository.save(application)
    return application.entity_id

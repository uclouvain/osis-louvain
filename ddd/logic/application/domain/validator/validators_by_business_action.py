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
from typing import List

import attr

from base.ddd.utils.business_validator import TwoStepsMultipleBusinessExceptionListValidator, BusinessValidator
from ddd.logic.application.commands import ApplyOnVacantCourseCommand, UpdateApplicationCommand
from ddd.logic.application.domain.model.applicant import Applicant
from ddd.logic.application.domain.model.application import Application
from ddd.logic.application.domain.model.vacant_course import VacantCourse
from ddd.logic.application.domain.validator._should_fields_be_required import ShouldFieldsBeRequiredValidator
from ddd.logic.application.domain.validator._should_lecturing_or_pratical_filled import \
    ShouldLecturingOrPracticalFilledValidator
from ddd.logic.application.domain.validator._should_not_have_already_applied_on_vacant_course import \
    ShouldNotHaveAlreadyAppliedOnVacantCourse


@attr.s(frozen=True, slots=True)
class ApplyOnVacantCourseValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    command = attr.ib(type=ApplyOnVacantCourseCommand)
    all_existing_applications = attr.ib(type=List[Application])
    applicant = attr.ib(type=Applicant)
    vacant_course = attr.ib(type=VacantCourse)

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return [
            ShouldFieldsBeRequiredValidator(self.command, 'code'),
            ShouldFieldsBeRequiredValidator(self.command, 'academic_year'),
            ShouldFieldsBeRequiredValidator(self.command, 'global_id'),
            ShouldLecturingOrPracticalFilledValidator(self.command)
        ]

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldNotHaveAlreadyAppliedOnVacantCourse(
                vacant_course=self.vacant_course, all_existing_applications=self.all_existing_applications
            )
        ]


@attr.s(frozen=True, slots=True)
class UpdateApplicationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    command = attr.ib(type=UpdateApplicationCommand)

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return [
            ShouldLecturingOrPracticalFilledValidator(self.command)
        ]

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return []

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

from base.ddd.utils.business_validator import BusinessValidator
from ddd.logic.application.domain.model.vacant_course import VacantCourse
from ddd.logic.application.domain.validator.exceptions import ApplicationAlreadyExistsException


@attr.s(frozen=True, slots=True)
class ShouldNotHaveAlreadyAppliedOnVacantCourse(BusinessValidator):
    vacant_course = attr.ib(type=VacantCourse)
    all_existing_applications = attr.ib(type=List['Application'])

    def validate(self, *args, **kwargs):
        if self.vacant_course in {application.vacant_course for application in self.all_existing_applications}:
            raise ApplicationAlreadyExistsException()

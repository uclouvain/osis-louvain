# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from base.ddd.utils import business_validator
from education_group.ddd.business_types import *
from education_group.ddd.domain.exception import TrainingHaveEnrollments, MiniTrainingHaveEnrollments
from education_group.ddd.domain.service.enrollment_counter import EnrollmentCounter


class TrainingEnrollmentsValidator(business_validator.BusinessValidator):
    def __init__(self, training_id: 'TrainingIdentity'):
        super().__init__()
        self.training_id = training_id

    def validate(self, *args, **kwargs):
        enrollments_count = EnrollmentCounter().get_training_enrollments_count(self.training_id)
        if enrollments_count > 0:
            raise TrainingHaveEnrollments(enrollments_count)


class MiniTrainingEnrollmentsValidator(business_validator.BusinessValidator):
    def __init__(self, mini_training_id: 'MiniTrainingIdentity'):
        super().__init__()
        self.mini_training_id = mini_training_id

    def validate(self, *args, **kwargs):
        enrollments_count = EnrollmentCounter().get_mini_training_enrollments_count(self.mini_training_id)
        if enrollments_count > 0:
            raise MiniTrainingHaveEnrollments(enrollments_count)

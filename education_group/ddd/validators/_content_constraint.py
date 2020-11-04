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
from typing import Optional

from base.ddd.utils import business_validator
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain.exception import ContentConstraintTypeMissing, ContentConstraintMinimumMaximumMissing, \
    ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum, ContentConstraintMinimumInvalid, \
    ContentConstraintMaximumInvalid

MIN_CONSTRAINT_VALUE = 1
MAX_CONSTRAINT_VALUE = 99999999999999


class ContentConstraintValidator(business_validator.BusinessValidator):
    def __init__(self, content_constraint: Optional[ContentConstraint]):
        super().__init__()
        self.content_constraint = content_constraint

    def validate(self, *args, **kwargs):
        if self.content_constraint is None:
            return

        if self.content_constraint.type is None and \
           (self.content_constraint.minimum is not None or self.content_constraint.maximum is not None):
            raise ContentConstraintTypeMissing

        if self.content_constraint.type and \
           (self.content_constraint.maximum is None and self.content_constraint.minimum is None):
            raise ContentConstraintMinimumMaximumMissing

        if self.content_constraint.minimum is not None and self.content_constraint.maximum is not None and \
                self.content_constraint.minimum > self.content_constraint.maximum:
            raise ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum

        if self.content_constraint.type and \
                (self.content_constraint.minimum and (
                        self.content_constraint.minimum < MIN_CONSTRAINT_VALUE or
                        self.content_constraint.minimum > MAX_CONSTRAINT_VALUE
                )):
            raise ContentConstraintMinimumInvalid

        if self.content_constraint.type and \
                (self.content_constraint.maximum and (
                        self.content_constraint.maximum < MIN_CONSTRAINT_VALUE or
                        self.content_constraint.maximum > MAX_CONSTRAINT_VALUE
                )):
            raise ContentConstraintMaximumInvalid

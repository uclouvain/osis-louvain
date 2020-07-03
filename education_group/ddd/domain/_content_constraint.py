##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional

from base.models.enums.constraint_type import ConstraintTypeEnum
from osis_common.ddd import interface


class ContentConstraint(interface.ValueObject):
    def __init__(self, type: Optional[ConstraintTypeEnum], minimum: Optional[int], maximum: Optional[int]):
        self.type = type
        self.minimum = minimum
        self.maximum = maximum

    def __eq__(self, other):
        return self.type == other.type \
               and self.minimum == other.minimum \
               and self.maximum == other.maximum

    def __hash__(self):
        return hash(str(self.type) + str(self.minimum) + str(self.maximum))

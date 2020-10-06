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
from typing import List

import attr

from osis_common.ddd import interface


class DiplomaAimIdentity(interface.EntityIdentity):

    def __init__(self, section: int, code: int):
        self.section = section
        self.code = code

    def __eq__(self, other):
        return self.section == other.section \
               and self.code == other.code

    def __hash__(self):
        return hash(str(self.section) + str(self.code))


class DiplomaAim(interface.Entity):

    def __init__(self, entity_id: DiplomaAimIdentity, description: str):
        super(DiplomaAim, self).__init__(entity_id=entity_id)
        self.entity_id = entity_id
        self.description = description

    @property
    def section(self) -> int:
        return self.entity_id.section

    @property
    def code(self) -> int:
        return self.entity_id.code

    def __str__(self):
        return "{} - {} {}".format(self.section, self.code, self.description)


@attr.s(frozen=True, slots=True)
class Diploma(interface.ValueObject):
    aims = attr.ib(type=List['DiplomaAim'])
    leads_to_diploma = attr.ib(type=bool, default=False)
    printing_title = attr.ib(type=str, default='')
    professional_title = attr.ib(type=str, default='')

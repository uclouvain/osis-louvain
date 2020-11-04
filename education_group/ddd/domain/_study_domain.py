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
import attr

from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class StudyDomainIdentity(interface.EntityIdentity):
    decree_name = attr.ib(type=str)
    code = attr.ib(type=str)


class StudyDomain(interface.Entity):
    def __init__(self, entity_id: StudyDomainIdentity, domain_name: str):
        super(StudyDomain, self).__init__(entity_id=entity_id)
        self.name = domain_name
        self.entity_id = entity_id

    @property
    def code(self) -> str:
        return self.entity_id.code

    @property
    def decree_name(self) -> str:
        return self.entity_id.decree_name

    def __eq__(self, other):
        if type(other) == self.__class__:
            return self.entity_id == other.entity_id
        return False

    def __str__(self):
        return "{obj.decree_name} : {obj.code} {obj.name}".format(obj=self)

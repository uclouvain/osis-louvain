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
from osis_common.ddd import interface


class StudyDomain(interface.ValueObject):
    def __init__(self, decree_name: str, code: str, name: str):
        self.decree_name = decree_name
        self.code = code
        self.name = name

    def __str__(self):
        return "{obj.decree_name} : {obj.code} {obj.name}".format(obj=self)

    def __eq__(self, other):
        return self.decree_name == other.decree_name and self.code == other.code and self.name == other.name

    def __hash__(self):
        return hash(self.decree_name + self.code + self.name)

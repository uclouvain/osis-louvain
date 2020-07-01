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


# FIXME :: should move into another app ? (This domain object is a common object that will be used everywhere).
class AcademicYear:

    def __init__(self, year: int):
        self.year = year

    def __str__(self):
        return u"%s-%s" % (self.year, str(self.year + 1)[-2:])

    @property
    def is_even(self) -> bool:
        return self.year % 2 == 0

    @property
    def is_odd(self) -> bool:
        return self.year % 2 == 1

    def next(self) -> 'AcademicYear':
        return self.__class__(self.year + 1)

    def past(self) -> 'AcademicYear':
        return self.__class__(self.year - 1)

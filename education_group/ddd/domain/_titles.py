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


class Titles(interface.ValueObject):
    def __init__(
            self,
            title_fr: str,
            partial_title_fr: str = None,
            title_en: str = None,
            partial_title_en: str = None
    ):
        self.title_fr = title_fr
        self.partial_title_fr = partial_title_fr or ""
        self.title_en = title_en or ""
        self.partial_title_en = partial_title_en or ""

    def __eq__(self, other):
        return self.title_fr == other.title_fr and \
            self.partial_title_fr == other.partial_title_fr and \
            self.title_en == other.title_en and \
            self.partial_title_en == other.partial_title_en

    def __hash__(self):
        return hash(self.title_fr + self.partial_title_fr + self.title_en + self.partial_title_en)

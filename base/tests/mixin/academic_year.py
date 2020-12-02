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
from unittest.mock import patch

from base.models import academic_year


class AcademicYearMockMixin:
    """
        This mixin allow mocking function current_academic_year() / starting_academic_year()
        in order to decouple test from system time
    """
    def mock_academic_year(self, current_academic_year=None, starting_academic_year=None):
        self.patch_academic_year = patch.multiple(
            academic_year,
            current_academic_year=lambda: current_academic_year,
            starting_academic_year=lambda: starting_academic_year
        )
        self.patch_academic_year.start()
        self.addCleanup(self.patch_academic_year.stop)

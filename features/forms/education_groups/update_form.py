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
from base.models.academic_year import AcademicYear, LEARNING_UNIT_CREATION_SPAN_YEARS
from features.pages.education_group import pages


def fill_end_year(page: pages.UpdateTrainingPage, current_academic_year: AcademicYear):
    end_year_chosen = AcademicYear.objects.filter(
        year__gt=current_academic_year.year,
        year__lte=current_academic_year.year + LEARNING_UNIT_CREATION_SPAN_YEARS
    ).order_by('?').first()
    page.fin = str(end_year_chosen)
    return {"end_year": str(end_year_chosen)}

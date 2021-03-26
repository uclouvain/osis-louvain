##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from base.business.academic_calendar import AcademicEventCalendarHelper
from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import AcademicYear
from base.models.enums import academic_calendar_type


class LearningUnitEnrollmentCalendar(AcademicEventCalendarHelper):
    event_reference = academic_calendar_type.COURSE_ENROLLMENT

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        current_academic_year = AcademicYear.objects.current()
        academic_years = AcademicYear.objects.min_max_years(current_academic_year.year, current_academic_year.year + 6)

        for ac_year in academic_years:
            AcademicCalendar.objects.get_or_create(
                reference=cls.event_reference,
                data_year=ac_year,
                defaults={
                    "title": "Inscription aux cours",
                    "start_date": datetime.date(ac_year.year, 9, 1),
                    "end_date": datetime.date(ac_year.year, 10, 31),
                }
            )

##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
from django.test import TestCase
from base.models import academic_year
from base.models.academic_calendar import AcademicCalendar

start_date = datetime.datetime.now()
end_date = start_date.replace(year=start_date.year + 1)


class AcademicCalendarTest(TestCase):

    academic_year = None

    def setUp(self):
        academic_yr = academic_year.AcademicYear(year=2016, start_date=start_date, end_date=end_date)
        academic_yr.save()
        self.academic_year = academic_yr

    def test_save_without_functions_args(self):
        ac_cal = AcademicCalendar(academic_year=self.academic_year,
                                  title="A calendar event",
                                  start_date=start_date,
                                  end_date=end_date)
        self.assertRaises(ValueError, ac_cal.save)

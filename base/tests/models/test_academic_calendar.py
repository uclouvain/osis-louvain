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
from base.models import academic_calendar
from base.models.exceptions import FunctionArgumentMissingException, StartDateHigherThanEndDateException

start_date = datetime.datetime.now()
end_date = start_date.replace(year=start_date.year + 1)


def create_academic_year():
    academic_yr = academic_year.AcademicYear(year=start_date.year, start_date=start_date, end_date=end_date)
    academic_yr.save()
    return academic_yr


def create_academic_calendar(an_academic_year, start_date=datetime.date(2000, 1, 1), end_date= datetime.date(2099, 1, 1)):
    an_academic_calendar = academic_calendar.AcademicCalendar(academic_year=an_academic_year, start_date=start_date,
                                                              end_date=end_date)
    an_academic_calendar.save(functions=[])
    return an_academic_calendar


class AcademicCalendarTest(TestCase):

    def setUp(self):
        self.academic_year = create_academic_year()

    def test_save_without_functions_args(self):
        academic_cal = academic_calendar.AcademicCalendar(academic_year=self.academic_year,
                                                          title="A calendar event",
                                                          start_date=start_date,
                                                          end_date=end_date)
        self.assertRaises(FunctionArgumentMissingException, academic_cal.save)

    def test_start_date_higher_than_end_date(self):
        wrong_end_date = datetime.datetime.now()
        wrong_start_date = wrong_end_date.replace(year=start_date.year + 1)
        academic_cal = academic_calendar.AcademicCalendar(academic_year=self.academic_year,
                                                          title="A calendar event",
                                                          start_date=wrong_start_date,
                                                          end_date=wrong_end_date)
        self.assertRaises(StartDateHigherThanEndDateException, academic_cal.save, functions=[])

    def test_start_date_equal_to_end_date(self):
        wrong_end_date = datetime.datetime.now()
        wrong_start_date = wrong_end_date
        academic_cal = academic_calendar.AcademicCalendar(academic_year=self.academic_year,
                                                          title="A calendar event",
                                                          start_date=wrong_start_date,
                                                          end_date=wrong_end_date)
        self.assertRaises(StartDateHigherThanEndDateException, academic_cal.save, functions=[])

    def test_find_by_id(self):
        self.assertEqual(academic_calendar.find_by_id(333), None)

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
from base.models import academic_year, offer_year_calendar, academic_calendar, offer_year


start_date = datetime.datetime.now()
end_date = start_date.replace(year=start_date.year + 1)


def _create_academic_year_2016():
    academic_yr = academic_year.AcademicYear(year=2016, start_date=start_date, end_date=end_date)
    academic_yr.save()
    return academic_yr


def _create_academic_calendar_with_offer_year_calendars():
    academic_yr = _create_academic_year_2016()
    academic_cal = academic_calendar.AcademicCalendar(academic_year=academic_yr,
                                                      title="a Title",
                                                      description="My offerYearCalendars are not customized (default value)",
                                                      start_date=start_date,
                                                      end_date=end_date)
    academic_cal.save(functions=[offer_year_calendar.save_from_academic_calendar])
    return academic_cal


class SaveFromAcademicCalendarTest(TestCase):

    def setUp(self):
        _create_academic_year_2016()

    def test_case_none_parameter(self):
        self.assertRaises(AttributeError, offer_year_calendar.save_from_academic_calendar, *[None])

    def test_case_not_yet_persistent_parameter(self):
        academic_yr = academic_year.AcademicYear.objects.all().first()
        academic_cal = academic_calendar.AcademicCalendar(academic_year=academic_yr,
                                                          title='A title',
                                                          description='A description',
                                                          start_date=start_date,
                                                          end_date=end_date)
        self.assertRaises(ValueError, offer_year_calendar.save_from_academic_calendar, *[academic_cal])


class AcademicCalendarWithoutOfferYearCalendar(TestCase):

    def setUp(self):
        academic_yr = _create_academic_year_2016()
        academic_cal = academic_calendar.AcademicCalendar(academic_year=academic_yr,
                                                          title="I don't have any offerYearCal",
                                                          start_date=start_date,
                                                          end_date=end_date)
        academic_cal.save(functions=[])

    def test_save_from_academic_calendar(self):
        academic_cal = academic_calendar.AcademicCalendar.objects.filter(title="I don't have any offerYearCal")\
                                                                 .first()
        self.assertEqual(len(offer_year_calendar.find_by_academic_calendar(academic_cal)), 0)
        offer_year_calendar.save_from_academic_calendar(academic_cal)
        self.assertEqual(len(offer_year_calendar.find_by_academic_calendar(academic_cal)),
                         len(offer_year.find_by_academic_year(academic_cal.academic_year)))


class AcademicCalendarWithOfferYearCalendarsCustomized(TestCase):

    academic_calendar = None

    def setUp(self):
        self.academic_calendar = _create_academic_calendar_with_offer_year_calendars()
        self.set_offer_year_calendars_customized()

    def set_offer_year_calendars_customized(self):
        random_start_date = datetime.datetime(2010, 4, 1, 16, 8, 18)
        random_end_date = random_start_date.replace(year=random_start_date.year + 1)
        offer_year_calendars = offer_year_calendar.OfferYearCalendar.objects.filter(academic_calendar=self.academic_calendar)
        for off_cal in offer_year_calendars:
            off_cal.customized = True
            off_cal.start_date = random_start_date
            off_cal.end_date = random_end_date
            off_cal.save()

    def test_save_from_academic_calendar(self):
        offer_year_calendars = offer_year_calendar.OfferYearCalendar.objects.filter(academic_calendar=self.academic_calendar,
                                                                                    customized=True)
        for off_y_cal in offer_year_calendars:
            self.assertEquals(off_y_cal.start_date, start_date)
            self.assertNotEquals(off_y_cal.end_date, end_date)


class AcademicCalendarWithOfferYearCalendarsNotCustomized(TestCase):

    academic_calendar = None

    def setUp(self):
        self.academic_calendar = _create_academic_calendar_with_offer_year_calendars()
        self.set_offer_year_calendars_not_customized()

    def set_offer_year_calendars_not_customized(self):
        offer_year_calendars = offer_year_calendar.OfferYearCalendar.objects.filter(academic_calendar=self.academic_calendar)
        for off_cal in offer_year_calendars:
            off_cal.customized = False
            off_cal.save()

    def test_save_from_academic_calendar(self):
        offer_year_calendars = offer_year_calendar.OfferYearCalendar.objects.filter(academic_calendar=self.academic_calendar)
        for off_y_cal in offer_year_calendars:
            self.assertEquals(off_y_cal.start_date, start_date)
            self.assertEquals(off_y_cal.end_date, end_date)

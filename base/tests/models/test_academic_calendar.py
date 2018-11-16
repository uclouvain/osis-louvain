##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

from django.forms import model_to_dict
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from base.models import academic_calendar
from base.models.academic_calendar import find_dates_for_current_academic_year, is_academic_calendar_has_started
from base.models.enums import academic_calendar_type
from base.models.exceptions import StartDateHigherThanEndDateException
from base.signals.publisher import compute_all_scores_encodings_deadlines
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory, AcademicYearFakerFactory, \
    create_current_academic_year


class AcademicCalendarTest(TestCase):

    def test_start_date_higher_than_end_date(self):
        yr = timezone.now().year
        an_academic_year = AcademicYearFactory(year=yr)
        an_academic_calendar = AcademicCalendarFactory.build(academic_year=an_academic_year,
                                                             title="An event",
                                                             start_date=datetime.date(yr, 3, 4),
                                                             end_date=datetime.date(yr, 3, 3))
        self.assertRaises(StartDateHigherThanEndDateException, an_academic_calendar.save)

    def test_find_highlight_academic_calendar(self):
        an_academic_year = AcademicYearFakerFactory(start_date=timezone.now() - datetime.timedelta(days=10),
                                                    end_date=timezone.now() + datetime.timedelta(days=10))

        tmp_academic_calendar_1 = AcademicCalendarFactory(academic_year=an_academic_year, title="First calendar event")

        tmp_academic_calendar_2 = AcademicCalendarFactory(academic_year=an_academic_year, title="Second calendar event")

        null_academic_calendar = AcademicCalendarFactory(academic_year=an_academic_year,
                                                         title="A third event which is null",
                                                         highlight_description=None)

        empty_academic_calendar = AcademicCalendarFactory(academic_year=an_academic_year,
                                                          title="A third event which is null",
                                                          highlight_title="")

        db_academic_calendars = list(academic_calendar.find_highlight_academic_calendar())
        self.assertIsNotNone(db_academic_calendars)
        self.assertCountEqual(db_academic_calendars, [tmp_academic_calendar_1, tmp_academic_calendar_2])

    def test_find_academic_calendar_by_academic_year(self):
        tmp_academic_year = AcademicYearFactory()
        tmp_academic_calendar = AcademicCalendarFactory(academic_year=tmp_academic_year)
        db_academic_calendar = list(academic_calendar.find_academic_calendar_by_academic_year
                                    ([tmp_academic_year][0]))[0]
        self.assertIsNotNone(db_academic_calendar)
        self.assertEqual(db_academic_calendar, tmp_academic_calendar)

    def test_find_academic_calendar_by_academic_year_with_dates(self):
        tmp_academic_year = AcademicYearFactory(year=timezone.now().year)
        tmp_academic_calendar = AcademicCalendarFactory(academic_year=tmp_academic_year)
        db_academic_calendar = list(academic_calendar.find_academic_calendar_by_academic_year_with_dates
                                    (tmp_academic_year.id))[0]
        self.assertIsNotNone(db_academic_calendar)
        self.assertEqual(db_academic_calendar, tmp_academic_calendar)

    def test_compute_deadline_is_called_case_academic_calendar_save(self):
        with mock.patch.object(compute_all_scores_encodings_deadlines, 'send') as mock_method:
            AcademicCalendarFactory()
            self.assertTrue(mock_method.called)


class TestFindDatesForCurrentAcademicYear(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_calendar = AcademicCalendarFactory(academic_year=create_current_academic_year(),
                                                                reference=academic_calendar_type.EXAM_ENROLLMENTS)

    def test_when_no_matching_reference(self):
        dates = find_dates_for_current_academic_year(academic_calendar_type.TEACHING_CHARGE_APPLICATION)
        self.assertFalse(dates)

    def test_when_matched(self):
        dates = find_dates_for_current_academic_year(academic_calendar_type.EXAM_ENROLLMENTS)
        self.assertEqual(dates,
                         model_to_dict(self.current_academic_calendar,
                                       fields=("start_date", "end_date")))


class TestIsAcademicCalendarHasStarted(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.current_academic_calendar = AcademicCalendarFactory(
            academic_year=cls.current_academic_year,
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
        )

    def test_is_academic_calendar_has_started_case_no_date_args(self):
        self.assertTrue(is_academic_calendar_has_started(
            academic_year=self.current_academic_year,
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
        ))

    def test_is_academic_calendar_has_started_case_date_args_lower_than_ac_calendar_start(self):
        lower_date = self.current_academic_calendar.start_date - datetime.timedelta(days=5)
        self.assertFalse(is_academic_calendar_has_started(
            academic_year=self.current_academic_year,
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            date=lower_date
        ))

    def test_is_academic_calendar_has_started_case_date_args_higher_than_ac_calendar_start(self):
        higher_date = self.current_academic_calendar.start_date + datetime.timedelta(days=10)
        self.assertTrue(is_academic_calendar_has_started(
            academic_year=self.current_academic_year,
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            date=higher_date
        ))

    def test_project_calendar_types(self):
        excepted_project_calendar_types = (
            (academic_calendar_type.TESTING, _("Testing")),
        )
        self.assertCountEqual(
            academic_calendar_type.PROJECT_CALENDAR_TYPES,
            excepted_project_calendar_types
        )

    def test_calendar_types(self):
        self.assertCountEqual(
            academic_calendar_type.ACADEMIC_CALENDAR_TYPES +
            academic_calendar_type.PROJECT_CALENDAR_TYPES +
            academic_calendar_type.AD_HOC_CALENDAR_TYPES,
            academic_calendar_type.CALENDAR_TYPES
        )


class TestGetStartingAcademicCalendar(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        end_date = today + datetime.timedelta(weeks=10)

        cls.academic_calendars_in_4_day = [
            AcademicCalendarFactory(start_date=today + datetime.timedelta(days=4), end_date=end_date) for _ in range(3)
        ]

        cls.academic_calendars_in_2_weeks = [
            AcademicCalendarFactory(start_date=today + datetime.timedelta(weeks=2), end_date=end_date) for _ in range(3)
        ]

        cls.academic_calendars_in_1_week_and_3_days = [
            AcademicCalendarFactory(start_date=today + datetime.timedelta(days=3, weeks=1), end_date=end_date)
            for _ in range(3)
        ]

    def test_when_inputing_nothing(self):
        qs = academic_calendar.AcademicCalendar.objects.starting_within()
        self.assertEqual(list(qs), [])

    def test_when_inputing_only_days(self):
        qs = academic_calendar.AcademicCalendar.objects.starting_within(days=5)
        self.assertCountEqual(list(qs),
                              self.academic_calendars_in_4_day)

        qs = academic_calendar.AcademicCalendar.objects.starting_within(days=10)
        self.assertCountEqual(list(qs),
                              self.academic_calendars_in_4_day + self.academic_calendars_in_1_week_and_3_days)

    def test_when_inputing_only_weeks(self):
        qs = academic_calendar.AcademicCalendar.objects.starting_within(weeks=1)
        self.assertCountEqual(list(qs),
                              self.academic_calendars_in_4_day)

        qs = academic_calendar.AcademicCalendar.objects.starting_within(weeks=2)
        self.assertCountEqual(list(qs),
                              self.academic_calendars_in_4_day + self.academic_calendars_in_1_week_and_3_days +
                              self.academic_calendars_in_2_weeks)

    def test_when_inputing_days_and_weeks(self):
        qs = academic_calendar.AcademicCalendar.objects.starting_within(weeks=1, days=2)
        self.assertCountEqual(list(qs),
                              self.academic_calendars_in_4_day)

        qs = academic_calendar.AcademicCalendar.objects.starting_within(weeks=1, days=5)
        self.assertCountEqual(list(qs),
                              self.academic_calendars_in_4_day + self.academic_calendars_in_1_week_and_3_days)

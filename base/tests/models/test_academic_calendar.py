##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import TestCase
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from faker import Faker

from base.models import academic_calendar
from base.models.academic_calendar import get_academic_calendar_by_date_and_reference_and_data_year, AcademicCalendar
from base.models.enums import academic_calendar_type
from base.models.enums.academic_calendar_type import EXAM_ENROLLMENTS, SCORES_EXAM_SUBMISSION
from base.models.exceptions import StartDateHigherThanEndDateException
from base.signals.publisher import compute_all_scores_encodings_deadlines
from base.tests.factories.academic_calendar import AcademicCalendarFactory, OpenAcademicCalendarFactory, \
    CloseAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year


class AcademicCalendarTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_start_date_higher_than_end_date(self):
        fake = Faker()
        with self.assertRaises(StartDateHigherThanEndDateException):
            AcademicCalendarFactory(start_date=fake.future_date(), end_date=fake.past_date())

    def test_find_highlight_academic_calendar(self):
        open_academic_calendar = OpenAcademicCalendarFactory()
        CloseAcademicCalendarFactory()
        OpenAcademicCalendarFactory(highlight_description=None)
        OpenAcademicCalendarFactory(highlight_title="")

        self.assertQuerysetEqual(
            academic_calendar.find_highlight_academic_calendar(),
            [open_academic_calendar],
            transform=lambda rec: rec
        )

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

    def test_get_academic_calendar_by_date_and_reference_and_data_year_exists(self):
        fake = Faker()
        data_year = AcademicYearFactory()
        cal = AcademicCalendarFactory(
            start_date=fake.past_date(),
            end_date=fake.future_date(),
            reference=EXAM_ENROLLMENTS,
            data_year=data_year
        )
        self.assertEqual(
            get_academic_calendar_by_date_and_reference_and_data_year(data_year, EXAM_ENROLLMENTS),
            cal
        )

    def test_get_academic_calendar_by_date_and_reference_and_data_year_none(self):
        AcademicCalendar.objects.filter(reference=EXAM_ENROLLMENTS).delete()
        fake = Faker()
        data_year = AcademicYearFactory()
        AcademicCalendarFactory(
            start_date=fake.past_date(),
            end_date=fake.future_date(),
            reference=SCORES_EXAM_SUBMISSION,
            data_year=data_year
        )
        self.assertEqual(
            get_academic_calendar_by_date_and_reference_and_data_year(data_year, EXAM_ENROLLMENTS),
            None
        )


class TestIsAcademicCalendarHasStarted(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.current_academic_calendar = AcademicCalendarFactory(
            academic_year=cls.current_academic_year,
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
        )

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

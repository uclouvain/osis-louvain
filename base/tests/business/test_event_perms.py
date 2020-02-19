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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.test import TestCase

from base.business import event_perms
from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory, AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory


class TestEventPerms(TestCase):
    def test_get_current_or_previous_opened_calendar_academic_years_calendar_opened(self):
        AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2017),
            start_date=datetime.date.today() - datetime.timedelta(weeks=104),
            end_date=datetime.date.today() - datetime.timedelta(weeks=100)
        )
        previous_calendar = AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2018),
            start_date=datetime.date.today() - datetime.timedelta(weeks=52),
            end_date=datetime.date.today() - datetime.timedelta(weeks=48)
        )
        AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2020),
            start_date=datetime.date.today() + datetime.timedelta(weeks=48),
            end_date=datetime.date.today() + datetime.timedelta(weeks=52)
        )
        OpenAcademicCalendarFactory(reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)
        event_perm = event_perms.EventPermSummaryCourseSubmission()
        self.assertEqual(
            previous_calendar,
            event_perm.get_previous_opened_calendar()
        )

    def test_get_current_or_previous_opened_calendar_academic_years_calendar_closed(self):
        AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2017),
            start_date=datetime.date.today() - datetime.timedelta(weeks=104),
            end_date=datetime.date.today() - datetime.timedelta(weeks=100)
        )
        previous_calendar = AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2018),
            start_date=datetime.date.today() - datetime.timedelta(weeks=52),
            end_date=datetime.date.today() - datetime.timedelta(weeks=48)
        )
        AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2020),
            start_date=datetime.date.today() + datetime.timedelta(weeks=48),
            end_date=datetime.date.today() + datetime.timedelta(weeks=52)
        )
        event_perm = event_perms.EventPermSummaryCourseSubmission()
        self.assertEqual(
            previous_calendar,
            event_perm.get_previous_opened_calendar()
        )

    def test_get_current_or_previous_opened_calendar_academic_years_only_future_calendar(self):
        AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2020),
            start_date=datetime.date.today() + datetime.timedelta(weeks=48),
            end_date=datetime.date.today() + datetime.timedelta(weeks=52)
        )
        event_perm = event_perms.EventPermSummaryCourseSubmission()
        self.assertIsNone(
            event_perm.get_previous_opened_calendar()
        )

    def test_get_current_or_previous_opened_calendar_academic_years_no_calendar(self):
        event_perm = event_perms.EventPermSummaryCourseSubmission()
        self.assertIsNone(
            event_perm.get_previous_opened_calendar()
        )
        self.assertIsNone(
            event_perm.get_next_opened_calendar()
        )

    def test_get_current_or_next_opened_calendar_academic_years_calendar_opened(self):
        AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2019),
            start_date=datetime.date.today() - datetime.timedelta(weeks=52),
            end_date=datetime.date.today() - datetime.timedelta(weeks=48)
        )
        next_calendar = AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2020),
            start_date=datetime.date.today() + datetime.timedelta(weeks=48),
            end_date=datetime.date.today() + datetime.timedelta(weeks=52)
        )
        AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2021),
            start_date=datetime.date.today() + datetime.timedelta(weeks=100),
            end_date=datetime.date.today() + datetime.timedelta(weeks=104)
        )
        OpenAcademicCalendarFactory(reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)
        event_perm = event_perms.EventPermSummaryCourseSubmission()
        self.assertEqual(
            next_calendar,
            event_perm.get_next_opened_calendar()
        )

    def test_get_current_or_next_opened_calendar_academic_years_calendar_closed(self):
        AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2019),
            start_date=datetime.date.today() - datetime.timedelta(weeks=52),
            end_date=datetime.date.today() - datetime.timedelta(weeks=48)
        )
        next_calendar = AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2020),
            start_date=datetime.date.today() + datetime.timedelta(weeks=48),
            end_date=datetime.date.today() + datetime.timedelta(weeks=52)
        )
        AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2021),
            start_date=datetime.date.today() + datetime.timedelta(weeks=100),
            end_date=datetime.date.today() + datetime.timedelta(weeks=104)
        )
        event_perm = event_perms.EventPermSummaryCourseSubmission()
        self.assertEqual(
            next_calendar,
            event_perm.get_next_opened_calendar()
        )

    def test_get_current_or_next_opened_calendar_academic_years_only_future_calendar(self):
        AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year=AcademicYearFactory(year=2018),
            start_date=datetime.date.today() - datetime.timedelta(weeks=52),
            end_date=datetime.date.today() - datetime.timedelta(weeks=48)
        )
        event_perm = event_perms.EventPermSummaryCourseSubmission()
        self.assertIsNone(
            event_perm.get_next_opened_calendar()
        )

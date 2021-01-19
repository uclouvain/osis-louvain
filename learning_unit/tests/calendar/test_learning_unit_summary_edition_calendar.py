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

from django.forms import model_to_dict
from django.test import TestCase

from base.business.event_perms import AcademicEvent
from base.models.academic_calendar import AcademicCalendar
from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory, CloseAcademicCalendarFactory, \
    AcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from learning_unit.calendar.learning_unit_summary_edition_calendar import LearningUnitSummaryEditionCalendar


class TestLearningUnitSummaryEditionCalendarEnsureConsistencyUntilNPlus6(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        AcademicYearFactory.produce_in_future(cls.current_academic_year.year)

    def test_ensure_consistency_until_n_plus_6_assert_default_value(self):
        LearningUnitSummaryEditionCalendar.ensure_consistency_until_n_plus_6()

        qs = AcademicCalendar.objects.filter(reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)

        self.assertEqual(qs.count(), 7)
        self.assertDictEqual(
            model_to_dict(qs.first(), fields=('title', 'reference', 'data_year', 'start_date', 'end_date')),
            {
                "title": "Edition fiches descriptives",
                "reference": academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
                "data_year": self.current_academic_year.pk,
                "start_date": datetime.date(self.current_academic_year.year, 7, 1),
                "end_date": datetime.date(self.current_academic_year.year, 9, 13),
            }
        )

    def test_ensure_consistency_until_n_plus_6_assert_idempotent(self):
        for _ in range(5):
            LearningUnitSummaryEditionCalendar.ensure_consistency_until_n_plus_6()

        self.assertEqual(
            AcademicCalendar.objects.filter(
                reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
            ).count(),
            7
        )


class TestLearningUnitSummaryEditionCalendarGetOpenedAcademicEvents(TestCase):
    def test_get_opened_academic_events_case_no_academic_events_opened(self):
        CloseAcademicCalendarFactory(reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)

        calendar = LearningUnitSummaryEditionCalendar()
        self.assertListEqual(calendar.get_opened_academic_events(), [])

    def test_get_opened_academic_events_case_one_academic_events_opened(self):
        academic_calendar_db = OpenAcademicCalendarFactory(reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)

        calendar = LearningUnitSummaryEditionCalendar()
        self.assertListEqual(
            calendar.get_opened_academic_events(),
            [
                AcademicEvent(
                    title=academic_calendar_db.title,
                    authorized_target_year=academic_calendar_db.data_year.year,
                    start_date=academic_calendar_db.start_date,
                    end_date=academic_calendar_db.end_date,
                )
            ]
        )

    def test_get_opened_academic_events_case_multiple_academic_events_opened(self):
        academic_calendar_db_2020 = OpenAcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year__year=2020,
            start_date=datetime.date(2020, 1, 12)
        )
        academic_calendar_db_2019 = OpenAcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            data_year__year=2019,
            start_date=datetime.date(2019, 1, 12)
        )

        calendar = LearningUnitSummaryEditionCalendar()
        # Ensure order is correct (order by start date)
        self.assertListEqual(
            calendar.get_opened_academic_events(),
            [
                AcademicEvent(
                    title=academic_calendar_db_2019.title,
                    authorized_target_year=academic_calendar_db_2019.data_year.year,
                    start_date=academic_calendar_db_2019.start_date,
                    end_date=academic_calendar_db_2019.end_date,
                ),
                AcademicEvent(
                    title=academic_calendar_db_2020.title,
                    authorized_target_year=academic_calendar_db_2020.data_year.year,
                    start_date=academic_calendar_db_2020.start_date,
                    end_date=academic_calendar_db_2020.end_date,
                )
            ]
        )


class TestLearningUnitSummaryEditionCalendarGetNextAcademicEvent(TestCase):
    def test_get_next_academic_event_case_no_next_academic_event(self):
        CloseAcademicCalendarFactory(reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)

        calendar = LearningUnitSummaryEditionCalendar()
        self.assertIsNone(calendar.get_next_academic_event())

    def test_get_next_academic_event_case_next_academic_event(self):
        academic_calendar_db = AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            start_date=datetime.date.today() + datetime.timedelta(days=5),
            end_date=datetime.date.today() + datetime.timedelta(days=10),
        )

        calendar = LearningUnitSummaryEditionCalendar()
        self.assertEqual(
            calendar.get_next_academic_event(),
            AcademicEvent(
                title=academic_calendar_db.title,
                authorized_target_year=academic_calendar_db.data_year.year,
                start_date=academic_calendar_db.start_date,
                end_date=academic_calendar_db.end_date,
            ),
        )


class TestLearningUnitSummaryEditionCalendarGetPreviousAcademicEvent(TestCase):
    def test_get_previous_academic_event_case_no_previous_academic_event(self):
        calendar = LearningUnitSummaryEditionCalendar()
        self.assertIsNone(calendar.get_previous_academic_event())

    def test_get_previous_academic_event_case_one_previous_academic_event(self):
        OpenAcademicCalendarFactory(reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)
        academic_calendar_db = AcademicCalendarFactory(
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            start_date=datetime.date.today() - datetime.timedelta(days=15),
            end_date=datetime.date.today() - datetime.timedelta(days=10),
        )

        calendar = LearningUnitSummaryEditionCalendar()
        self.assertEqual(
            calendar.get_previous_academic_event(),
            AcademicEvent(
                title=academic_calendar_db.title,
                authorized_target_year=academic_calendar_db.data_year.year,
                start_date=academic_calendar_db.start_date,
                end_date=academic_calendar_db.end_date,
            ),
        )

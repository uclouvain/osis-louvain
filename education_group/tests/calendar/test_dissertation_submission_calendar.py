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

from base.business.academic_calendar import AcademicSessionEvent
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.session_exam_calendar import SessionExamCalendar
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from education_group.calendar.dissertation_submission_calendar import DissertationSubmissionCalendar


class TestDissertationSubmissionCalendarEnsureConsistencyUntilNPlus6(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        AcademicYearFactory.produce_in_future(cls.current_academic_year.year)

    def test_ensure_consistency_until_n_plus_6_assert_default_value(self):
        DissertationSubmissionCalendar.ensure_consistency_until_n_plus_6()

        qs = AcademicCalendar.objects.filter(reference=AcademicCalendarTypes.DISSERTATION_SUBMISSION.name)

        self.assertEqual(qs.count(), 21)  # There are 3 sessions (7*3 = 21)

        first_session_academic_calendar = qs.first()
        self.assertDictEqual(
            model_to_dict(
                first_session_academic_calendar,
                fields=('title', 'reference', 'data_year', 'start_date', 'end_date')
            ),
            {
                "title": "Remise du mémoire - Session 1",
                "reference": AcademicCalendarTypes.DISSERTATION_SUBMISSION.name,
                "data_year": self.current_academic_year.pk,
                "start_date": datetime.date(self.current_academic_year.year, 12, 1),
                "end_date": datetime.date(self.current_academic_year.year + 1, 1, 31),
            }
        )

        session_exam_calendar = SessionExamCalendar.objects.get(academic_calendar=first_session_academic_calendar)
        self.assertEqual(session_exam_calendar.number_session, 1)

    def test_ensure_consistency_until_n_plus_6_assert_idempotent(self):
        for _ in range(5):
            DissertationSubmissionCalendar.ensure_consistency_until_n_plus_6()

        self.assertEqual(
            AcademicCalendar.objects.filter(
                reference=AcademicCalendarTypes.DISSERTATION_SUBMISSION.name
            ).count(),
            21
        )

        self.assertEqual(
            SessionExamCalendar.objects.filter(
                academic_calendar__reference=AcademicCalendarTypes.DISSERTATION_SUBMISSION.name
            ).count(),
            21
        )


class TestDissertationSubmissionCalendarGetAcademicSessionEvent(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()

        cls.academic_calendar = OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.DISSERTATION_SUBMISSION.name,
            data_year__year=2020
        )
        SessionExamCalendarFactory(number_session=1, academic_calendar=cls.academic_calendar)

    def test_get_academic_session_event_case_opened(self):
        calendar = DissertationSubmissionCalendar()

        academic_session_event = calendar.get_academic_session_event(target_year=2020, session=1)
        self.assertIsInstance(academic_session_event, AcademicSessionEvent)
        self.assertEqual(
            academic_session_event,
            AcademicSessionEvent(
                id=self.academic_calendar.pk,
                session=1,
                authorized_target_year=2020,
                title=self.academic_calendar.title,
                start_date=self.academic_calendar.start_date,
                end_date=self.academic_calendar.end_date,
                type=self.academic_calendar.reference
            )
        )

    def test_get_academic_session_event_case_no_calendar(self):
        calendar = DissertationSubmissionCalendar()

        self.assertIsNone(
            calendar.get_academic_session_event(target_year=2020, session=2)
        )

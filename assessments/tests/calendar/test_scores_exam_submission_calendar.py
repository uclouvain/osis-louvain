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

from assessments.calendar.scores_exam_submission_calendar import ScoresExamSubmissionCalendar
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.session_exam_calendar import SessionExamCalendar
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory


class TestScoreExamDiffusionCalendarEnsureConsistencyUntilNPlus6(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        AcademicYearFactory.produce_in_future(cls.current_academic_year.year)

    def test_ensure_consistency_until_n_plus_6_assert_default_value(self):
        ScoresExamSubmissionCalendar.ensure_consistency_until_n_plus_6()

        qs = AcademicCalendar.objects.filter(reference=AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name)

        self.assertEqual(qs.count(), 21)  # There are 3 sessions (7*3 = 21)

        first_session_academic_calendar = qs.first()
        self.assertDictEqual(
            model_to_dict(
                first_session_academic_calendar,
                fields=('title', 'reference', 'data_year', 'start_date', 'end_date')
            ),
            {
                "title": "Encodage de notes - Session 1",
                "reference": AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name,
                "data_year": self.current_academic_year.pk,
                "start_date": datetime.date(self.current_academic_year.year, 12, 15),
                "end_date": datetime.date(self.current_academic_year.year + 1, 2, 28),
            }
        )

        session_exam_calendar = SessionExamCalendar.objects.get(academic_calendar=first_session_academic_calendar)
        self.assertEqual(session_exam_calendar.number_session, 1)

    def test_ensure_consistency_until_n_plus_6_assert_idempotent(self):
        for _ in range(5):
            ScoresExamSubmissionCalendar.ensure_consistency_until_n_plus_6()

        self.assertEqual(
            AcademicCalendar.objects.filter(
                reference=AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name
            ).count(),
            21
        )

        self.assertEqual(
            SessionExamCalendar.objects.filter(
                academic_calendar__reference=AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name
            ).count(),
            21
        )

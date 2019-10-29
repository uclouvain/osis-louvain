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

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.test.utils import override_settings

from base.models import academic_year
from base.models import session_exam_calendar
from base.models.enums import number_session, academic_calendar_type
from base.models.session_exam_calendar import get_number_session_by_academic_calendar
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory


class SessionExamCalendarTest(TestCase):
    def setUp(self):
        AcademicYearFactory.produce_in_past()

        self.current_academic_yr = academic_year.current_academic_year()

        self.academic_calendar_1 = AcademicCalendarFactory(title="Submission of score encoding - 1",
                                                           start_date=datetime.date(self.current_academic_yr.year, 10, 15),
                                                           end_date=datetime.date(self.current_academic_yr.year+1, 1, 1),
                                                           academic_year=self.current_academic_yr,
                                                           reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        self.academic_calendar_2 = AcademicCalendarFactory(title="Submission of score encoding - 2",
                                                           start_date=datetime.date(self.current_academic_yr.year+1, 3, 15),
                                                           end_date=datetime.date(self.current_academic_yr.year+1, 6, 28),
                                                           academic_year=self.current_academic_yr,
                                                           reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        self.academic_calendar_3 = AcademicCalendarFactory(title="Submission of score encoding - 3",
                                                           start_date=datetime.date(self.current_academic_yr.year+1, 8, 1),
                                                           end_date=datetime.date(self.current_academic_yr.year+1, 9, 29),
                                                           academic_year=self.current_academic_yr,
                                                           reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        self.academic_calendar_4 = AcademicCalendarFactory(title="Deliberation session 1",
                                                           start_date=datetime.date(self.current_academic_yr.year+1, 1, 1),
                                                           end_date=datetime.date(self.current_academic_yr.year+1, 1, 2),
                                                           academic_year=self.current_academic_yr,
                                                           reference=academic_calendar_type.DELIBERATION)

    def test_number_exam_session_out_of_range(self):
        session_exam_calendar = SessionExamCalendarFactory.build(academic_calendar=self.academic_calendar_1,
                                                                 number_session=5)
        with self.assertRaises(ValidationError):
            session_exam_calendar.full_clean()

    def test_valid_number_exam_session(self):
        session_exam_calendar = SessionExamCalendarFactory.build(academic_calendar=self.academic_calendar_1,
                                                                 number_session=number_session.ONE)
        session_exam_calendar.full_clean()
        session_exam_calendar.save()

    def test_duplicate_exam_session(self):
        SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1, number_session=number_session.ONE)
        with self.assertRaises(IntegrityError):
            SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1, number_session=number_session.ONE)

    def test_current_session_exam(self):
        session = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                             number_session=number_session.ONE)

        self.assertEqual(session, session_exam_calendar.current_session_exam(date=datetime.date(self.current_academic_yr.year, 11, 9)))

    def test_current_session_exam_none(self):
        SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                   number_session=number_session.ONE)

        self.assertIsNone(session_exam_calendar.current_session_exam(date=datetime.date(self.current_academic_yr.year+1, 1, 5)))

    def test_find_session_exam_number(self):
        SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                   number_session=number_session.TWO)

        self.assertEqual(number_session.TWO,
                         session_exam_calendar.find_session_exam_number(date=datetime.date(self.current_academic_yr.year, 11, 9)))

    def test_find_session_exam_number_none(self):
        SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                   number_session=number_session.TWO)

        self.assertIsNone(session_exam_calendar.find_session_exam_number(date=datetime.date(self.current_academic_yr.year+1, 1, 5)))

    def test_get_latest_session_exam(self):


        #
        first = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                           number_session=number_session.ONE)
        second = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_2,
                                            number_session=number_session.TWO)
        third = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_3,
                                           number_session=number_session.THREE)

        self.assertIsNone(session_exam_calendar.get_latest_session_exam(date=datetime.date(self.current_academic_yr.year, 11, 15)))
        self.assertEqual(first, session_exam_calendar.get_latest_session_exam(date=datetime.date(self.current_academic_yr.year+1, 2, 10)))
        self.assertEqual(second, session_exam_calendar.get_latest_session_exam(date=datetime.date(self.current_academic_yr.year+1, 8, 15)))
        self.assertEqual(third, session_exam_calendar.get_latest_session_exam(date=datetime.date(self.current_academic_yr.year+2, 2, 2)))

    def get_closest_new_session_exam(self):
        first = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                           number_session=number_session.ONE)
        second = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_2,
                                            number_session=number_session.TWO)
        third = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_3,
                                           number_session=number_session.THREE)

        self.assertEqual(first, session_exam_calendar.get_closest_new_session_exam(date=datetime.date(self.current_academic_yr.year, 9, 15)))
        self.assertEqual(second, session_exam_calendar.get_closest_new_session_exam(date=datetime.date(self.current_academic_yr.year, 10, 17)))
        self.assertEqual(third, session_exam_calendar.get_closest_new_session_exam(date=datetime.date(self.current_academic_yr.year+1, 3, 16)))
        self.assertIsNone(session_exam_calendar.get_closest_new_session_exam(date=datetime.date(self.current_academic_yr.year+1, 10, 16)))

    def test_get_number_session_by_academic_calendar_empty(self):
        number = get_number_session_by_academic_calendar(self.academic_calendar_1)
        self.assertEqual(number, None)

    def test_get_number_session_by_academic_calendar(self):
        SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                           number_session=number_session.ONE)
        number = get_number_session_by_academic_calendar(self.academic_calendar_1)
        self.assertEqual(number, number_session.ONE)


class DeliberationDateTest(TestCase):
    def setUp(self):
        AcademicYearFactory.produce_in_past()

        self.current_academic_yr = academic_year.current_academic_year()
        self.academic_calendar = AcademicCalendarFactory(title="Deliberation session 1",
                                                         start_date=datetime.date(self.current_academic_yr.year+1, 1, 1),
                                                         end_date=datetime.date(self.current_academic_yr.year+1, 1, 2),
                                                         academic_year=self.current_academic_yr,
                                                         reference=academic_calendar_type.DELIBERATION)
        SessionExamCalendarFactory(academic_calendar=self.academic_calendar,
                                   number_session=number_session.ONE)
        self.offer_yr = OfferYearFactory(academic_year=self.current_academic_yr)

    @override_settings(USE_TZ=False)
    def test_taking_correct_number_session(self):
        offer_year_cal = OfferYearCalendarFactory(academic_calendar=self.academic_calendar,
                                                  offer_year=self.offer_yr)
        self.assertEqual(session_exam_calendar.find_deliberation_date(number_session.ONE,offer_year_cal.offer_year),
                         datetime.datetime(self.current_academic_yr.year+1, 1, 1))
        self.assertIsNone(session_exam_calendar.find_deliberation_date(number_session.TWO, offer_year_cal.offer_year))

    @override_settings(USE_TZ=False)
    def test_case_deliberation_date_is_set(self):
        delibe_date = datetime.datetime(self.current_academic_yr.year+1, 6, 10)
        offer_year_cal = OfferYearCalendarFactory(academic_calendar=self.academic_calendar,
                                                  offer_year=self.offer_yr,
                                                  start_date=delibe_date,
                                                  end_date=delibe_date)
        self.assertEqual(session_exam_calendar.find_deliberation_date(number_session.ONE, offer_year_cal.offer_year), delibe_date)

    @override_settings(USE_TZ=False)
    def test_case_deliberation_date_is_not_set(self):
        global_date = self.academic_calendar.start_date
        delibe_date = None
        OfferYearCalendarFactory(academic_calendar=self.academic_calendar,
                                 offer_year=self.offer_yr,
                                 start_date=delibe_date,
                                 end_date=delibe_date)
        result_delibe_date = session_exam_calendar.find_deliberation_date(number_session.ONE, self.offer_yr)
        self.assertNotEqual(result_delibe_date, global_date)
        self.assertIsNone(result_delibe_date)



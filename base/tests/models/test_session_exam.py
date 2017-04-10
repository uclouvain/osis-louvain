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

from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.session_examen import SessionExamFactory
from base.tests.models import test_offer_year, test_learning_unit_year, test_academic_calendar
from base.models import academic_year, session_exam, offer_year_calendar
from django.test import TestCase


def create_session_exam(number_session, learning_unit_year, offer_year_calendar):
    a_session_exam = session_exam.SessionExam(number_session=number_session,
                                              learning_unit_year=learning_unit_year,
                                              offer_year_calendar=offer_year_calendar)
    a_session_exam.save()
    return a_session_exam


class IsInsideScoreEncoding(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory(year=1900,
                                                 start_date=datetime.datetime(1900, 1, 1),
                                                 end_date=datetime.datetime(1900, 12, 28))
        self.academic_calendar = AcademicCalendarFactory.build(academic_year=self.academic_year,
                                                               start_date=datetime.datetime(1900, 1, 1),
                                                               end_date=datetime.datetime(1900, 12, 28))
        self.academic_calendar.save(functions=[])
        self.offer_year = OfferYearFactory(academic_year=self.academic_year)
        self.offer_year_calendar = OfferYearCalendarFactory(offer_year=self.offer_year,
                                                            academic_calendar=self.academic_calendar,
                                                            start_date=datetime.datetime(1900, 1, 1),
                                                            end_date=datetime.datetime(1900, 12, 28))
        self.learning_unit_year = LearningUnitYearFactory(academic_year=self.academic_year)
        self.session_exam = SessionExamFactory.build(number_session=1, learning_unit_year=self.learning_unit_year,
                                                     offer_year_calendar=self.offer_year_calendar)
        self.session_exam.save()

    def test_is_inside_score_encoding(self):
        is_inside = session_exam.is_inside_score_encoding(date=datetime.datetime(1900, 2, 2))
        self.assertTrue(is_inside)

    def test_is_not_inside_score_encoding_below(self):
        is_inside = session_exam.is_inside_score_encoding(date=datetime.datetime(1899, 12, 30))
        self.assertFalse(is_inside)

    def test_is_not_inside_score_encoding_upper(self):
        is_inside = session_exam.is_inside_score_encoding(date=datetime.datetime(1900, 12, 29))
        self.assertFalse(is_inside)


class GetLatestSessionExam(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory(year=1901,
                                                 start_date=datetime.datetime(1901, 9, 15),
                                                 end_date=datetime.datetime(1902, 9, 14))
        self.learning_unit_year = LearningUnitYearFactory(academic_year=self.academic_year)


        self.academic_calendar = AcademicCalendarFactory.build(title="Submission of exam scores - session 1",
                                                               academic_year=self.academic_year,
                                                               start_date=datetime.datetime(1901, 10, 15),
                                                               end_date=datetime.datetime(1902, 3, 28))
        self.academic_calendar.save(functions=[])
        self.academic_calendar_2 = AcademicCalendarFactory.build(title="Submission of exam scores - session 2",
                                                                 academic_year=self.academic_year,
                                                                 start_date=datetime.datetime(1902, 5, 19),
                                                                 end_date=datetime.datetime(1902, 10, 28))
        self.academic_calendar_2.save(functions=[])
        self.offer_year = OfferYearFactory(academic_year=self.academic_year)

        self.offer_year_calendar = OfferYearCalendarFactory(offer_year=self.offer_year,
                                                            academic_calendar=self.academic_calendar,
                                                            start_date=datetime.datetime(1901, 10,15),
                                                            end_date=datetime.datetime(1902, 3, 28))

        self.offer_year_calendar_2 = OfferYearCalendarFactory(offer_year=self.offer_year,
                                                              academic_calendar=self.academic_calendar_2,
                                                              start_date=None,
                                                              end_date=None)

        self.first_session = SessionExamFactory(number_session=1, learning_unit_year=self.learning_unit_year,
                                                offer_year_calendar=self.offer_year_calendar)
        self.second_session = SessionExamFactory(number_session=2, learning_unit_year=self.learning_unit_year,
                                                 offer_year_calendar=self.offer_year_calendar_2)

    def test_is_inside_score_encoding(self):
        is_inside = session_exam.is_inside_score_encoding(date=datetime.datetime(1901, 10, 16))
        self.assertTrue(is_inside)

    def test_is_not_inside_score_encoding(self):
        is_inside = session_exam.is_inside_score_encoding(date=datetime.datetime(1902, 4, 1))
        self.assertFalse(is_inside)

    def test_get_latest_session_exam_result_none(self):
        latest = session_exam.get_latest_session_exam(date=datetime.datetime(1901, 1, 2))
        self.assertIsNone(latest)

    def test_get_latest_session_exam_first_session(self):
        latest = session_exam.get_latest_session_exam(date=datetime.datetime(1902, 3, 29))
        self.assertEqual(latest, self.first_session)

    def test_get_closest_new_session_exam(self):
         latest = session_exam.get_closest_new_session_exam(date=datetime.datetime(1902, 4, 1))
         self.assertEqual(latest, self.second_session)

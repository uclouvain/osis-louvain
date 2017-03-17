##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils import timezone

from django.test import TestCase

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.session_examen import SessionExamFactory
from base.tests.factories.exam_enrollment import ExamEnrollmentFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollment as LearningUnitEnrollmentFactory


class EncodingClosedTest(TestCase):
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
        self.session_exam = SessionExamFactory.build(number_session=1,
                                                     learning_unit_year=self.learning_unit_year,
                                                     offer_year_calendar=self.offer_year_calendar)
        self.session_exam.save()
        self.student = StudentFactory(person=PersonFactory(last_name='Durant', first_name='Thomas'))
        self.offer_enrollment = OfferEnrollmentFactory(offer_year=self.offer_year, student=self.student)
        self.learning_unit_enrollment = LearningUnitEnrollmentFactory(learning_unit_year=self.learning_unit_year,
                                                                      offer_enrollment=self.offer_enrollment)
        self.exam_enrollment = ExamEnrollmentFactory(session_exam=self.session_exam,
                                                     learning_unit_enrollment=self.learning_unit_enrollment)

    def test_no_deadline(self):
        self.session_exam.deadline = None
        self.assertFalse(has_deadline(self.session_exam))

    def test_prior_deadline(self):
        self.session_exam.deadline = timezone.now() - timezone.timedelta(days=2)
        self.assertTrue(prior_deadline(self.session_exam.deadline))

    def test_post_deadline(self):
        self.session_exam.deadline = timezone.now() + timezone.timedelta(days=2)
        self.assertFalse(prior_deadline(self.session_exam.deadline))

    def test_score_missing(self):
        self.exam_enrollment.score_draft = None
        self.exam_enrollment.justification_draft = None
        self.exam_enrollment.score_final = None
        self.exam_enrollment.justification_final = None
        self.assertTrue(score_missing(self.exam_enrollment))

    def test_score_not_missing(self):
        self.exam_enrollment.score_draft = 10
        self.assertFalse(score_missing(self.exam_enrollment))

    def test_score_not_submitted(self):
        self.exam_enrollment.score_draft = 10
        self.exam_enrollment.justification_draft = None
        self.exam_enrollment.score_final = 10
        self.exam_enrollment.justification_final = 'T'
        self.assertFalse(score_submitted(self.exam_enrollment))

    def test_score_submitted(self):
        self.exam_enrollment.score_draft = 10
        self.exam_enrollment.justification_draft = 'T'
        self.exam_enrollment.score_final = 10
        self.exam_enrollment.justification_final = 'T'
        self.assertTrue(score_submitted(self.exam_enrollment))


def has_deadline(a_session_exam):
    if a_session_exam.deadline:
        return True
    return False


def prior_deadline(a_deadline):
    if a_deadline < timezone.now():
        return True
    return False


def score_missing(an_exam_enrollment):
    if is_score_empty(an_exam_enrollment) and is_justification_empty(an_exam_enrollment):
        return True
    return False


def is_score_empty(an_exam_enrollment):
    if an_exam_enrollment.score_draft is None and an_exam_enrollment.score_final is None:
        return True
    return False


def is_justification_empty(an_exam_enrollment):
    if an_exam_enrollment.justification_draft is None and an_exam_enrollment.justification_final is None:
        return True
    return False


def score_submitted(an_exam_enrollment):
    if not is_justification_empty(an_exam_enrollment) or not is_score_empty(an_exam_enrollment):
        if an_exam_enrollment.score_draft == an_exam_enrollment.score_final \
                and an_exam_enrollment.justification_draft == an_exam_enrollment.justification_final:
            return True
    return False






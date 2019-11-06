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

from django.test import TestCase

from base.models import exam_enrollment, exceptions
from base.models.enums import exam_enrollment_state as enrollment_states
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.exam_enrollment import ExamEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.session_exam_deadline import SessionExamDeadlineFactory
from base.tests.models import test_student, test_offer_enrollment, test_learning_unit_enrollment, \
    test_session_exam, test_offer_year


def create_exam_enrollment(session_exam, learning_unit_enrollment):
    an_exam_enrollment = exam_enrollment.ExamEnrollment(session_exam=session_exam,
                                                        learning_unit_enrollment=learning_unit_enrollment)
    an_exam_enrollment.save()
    return an_exam_enrollment


def create_exam_enrollment_with_student(num_id, registration_id, offer_year, learning_unit_year):
    student = test_student.create_student("Student" + str(num_id), "Etudiant" + str(num_id), registration_id)
    offer_enrollment = test_offer_enrollment.create_offer_enrollment(student, offer_year)
    learning_unit_enrollment = test_learning_unit_enrollment.create_learning_unit_enrollment(learning_unit_year,
                                                                                             offer_enrollment)
    session_exam = test_session_exam.create_session_exam(1, learning_unit_year, offer_year)
    return create_exam_enrollment(session_exam, learning_unit_enrollment)


class ExamEnrollmentTest(TestCase):
    def setUp(self):
        self.academic_year = create_current_academic_year()
        self.offer_year = test_offer_year.create_offer_year('SINF1BA', 'Bachelor in informatica', self.academic_year)
        self.learn_unit_year = LearningUnitYearFactory(acronym='LSINF1010',
                                                       specific_title='Introduction to algorithmic',
                                                       academic_year=self.academic_year)
        self.session_exam = test_session_exam.create_session_exam(1, self.learn_unit_year, self.offer_year)
        self.student = test_student.create_student('Pierre', 'Lacazette', '12345678')
        self.offer_enrollment = test_offer_enrollment.create_offer_enrollment(self.student, self.offer_year)
        self.learn_unit_enrol = test_learning_unit_enrollment.create_learning_unit_enrollment(self.learn_unit_year,
                                                                                              self.offer_enrollment)
        self.exam_enrollment = ExamEnrollmentFactory(session_exam=self.session_exam,
                                                     learning_unit_enrollment=self.learn_unit_enrol,
                                                     score_final=12.6,
                                                     enrollment_state=enrollment_states.ENROLLED)
        student_unsuscribed = test_student.create_student('Marco', 'Dubois', '12345679')
        offer_enrollment_2 = test_offer_enrollment.create_offer_enrollment(student_unsuscribed, self.offer_year)
        learn_unit_enrol_2 = test_learning_unit_enrollment.create_learning_unit_enrollment(self.learn_unit_year,
                                                                                           offer_enrollment_2)
        self.exam_enrollment_2 = ExamEnrollmentFactory(session_exam=self.session_exam,
                                                       learning_unit_enrollment=learn_unit_enrol_2,
                                                       enrollment_state=enrollment_states.NOT_ENROLLED)

    def test_save_with_invalid_justification_draft(self):
        ex_enrol = self.exam_enrollment
        ex_enrol.justification_draft = 'invalid_justification'
        self.assertRaises(exceptions.JustificationValueException, ex_enrol.save)

    def test_save_with_invalid_justification_final(self):
        ex_enrol = self.exam_enrollment
        ex_enrol.justification_final = 'invalid_justification'
        self.assertRaises(exceptions.JustificationValueException, ex_enrol.save)

    def test_save_with_invalid_justification_reencoded(self):
        ex_enrol = self.exam_enrollment
        ex_enrol.justification_reencoded = 'invalid_justification'
        self.assertRaises(exceptions.JustificationValueException, ex_enrol.save)

    def test_calculate_exam_enrollment_without_progress(self):
        self.assertEqual(exam_enrollment.calculate_exam_enrollment_progress(None), 0)

    def test_calculate_exam_enrollment_with_progress(self):
        ex_enrol = [self.exam_enrollment]
        progress = exam_enrollment.calculate_exam_enrollment_progress(ex_enrol)
        self.assertTrue(0 <= progress <= 100)

    def test_is_deadline_reached(self):
        self.exam_enrollment.save()
        SessionExamDeadlineFactory(deadline=datetime.date.today() - datetime.timedelta(days=1),
                                   number_session=self.session_exam.number_session,
                                   offer_enrollment=self.offer_enrollment)
        self.assertTrue(exam_enrollment.is_deadline_reached(self.exam_enrollment))

    def test_is_deadline_not_reached(self):
        self.exam_enrollment.save()
        SessionExamDeadlineFactory(deadline=datetime.date.today() + datetime.timedelta(days=2),
                                   number_session=self.session_exam.number_session,
                                   offer_enrollment=self.offer_enrollment)
        self.assertFalse(exam_enrollment.is_deadline_reached(self.exam_enrollment))

    def test_is_deadline_tutor_reached(self):
        self.exam_enrollment.save()
        SessionExamDeadlineFactory(deadline=datetime.date.today() + datetime.timedelta(days=3),
                                   deadline_tutor=5,
                                   number_session=self.session_exam.number_session,
                                   offer_enrollment=self.offer_enrollment)
        self.assertTrue(exam_enrollment.is_deadline_tutor_reached(self.exam_enrollment))

    def test_is_deadline_tutor_not_reached(self):
        self.exam_enrollment.save()
        SessionExamDeadlineFactory(deadline=datetime.date.today() + datetime.timedelta(days=3),
                                   deadline_tutor=2,
                                   number_session=self.session_exam.number_session,
                                   offer_enrollment=self.offer_enrollment)
        self.assertFalse(exam_enrollment.is_deadline_tutor_reached(self.exam_enrollment))

    def test_is_deadline_tutor_not_set_not_reached(self):
        self.exam_enrollment.save()
        SessionExamDeadlineFactory(deadline=datetime.date.today() + datetime.timedelta(days=3),
                                   deadline_tutor=None,
                                   number_session=self.session_exam.number_session,
                                   offer_enrollment=self.offer_enrollment)
        self.assertFalse(exam_enrollment.is_deadline_tutor_reached(self.exam_enrollment))

    def test_is_deadline_tutor_not_set_reached(self):
        self.exam_enrollment.save()
        SessionExamDeadlineFactory(deadline=datetime.date.today() - datetime.timedelta(days=1),
                                   deadline_tutor=None,
                                   number_session=self.session_exam.number_session,
                                   offer_enrollment=self.offer_enrollment)
        self.assertTrue(exam_enrollment.is_deadline_tutor_reached(self.exam_enrollment))

    def test_find_for_score_encodings_for_all_enrollement_state(self):
        self.assertCountEqual(exam_enrollment.find_for_score_encodings(
            session_exam_number=1,
        ), [self.exam_enrollment, self.exam_enrollment_2])

    def test_find_for_score_encodings_enrolled_state_only(self):
        self.assertCountEqual(exam_enrollment.find_for_score_encodings(
            session_exam_number=1,
            only_enrolled=True
        ), [self.exam_enrollment])

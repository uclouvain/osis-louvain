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
from datetime import timedelta, datetime
from unittest import mock

from django.test import TestCase

from assessments.business import scores_encodings_deadline
from base.models.enums import number_session, academic_calendar_type
from base.models.session_exam_deadline import SessionExamDeadline
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.session_exam_deadline import SessionExamDeadlineFactory
from base.tests.factories.student import StudentFactory


class ComputeScoresEncodingsDeadlinesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.nb_session = number_session.ONE
        current_year = datetime.now().year
        current_date = datetime(year=current_year, month=9, day=1, hour=12)
        cls.academic_year = AcademicYearFactory(year=current_year,
                                                start_date=current_date,
                                                end_date=current_date + timedelta(days=365))

        cls.off_year = OfferYearFactory()
        cls.education_group_year = EducationGroupYearFactory()
        cls.academic_calendar_deliberation = AcademicCalendarFactory(
            academic_year=cls.academic_year,
            reference=academic_calendar_type.DELIBERATION,
            start_date=cls.academic_year.start_date,
            end_date=cls.academic_year.end_date,
        )

        SessionExamCalendarFactory(
            academic_calendar=cls.academic_calendar_deliberation,
            number_session=cls.nb_session,
        )

    def setUp(self):
        self.offer_year_calendar_deliberation = OfferYearCalendarFactory(
            academic_calendar=self.academic_calendar_deliberation,
            offer_year=self.off_year,
            start_date=self.academic_calendar_deliberation.start_date,
            end_date=self.academic_calendar_deliberation.end_date,
            education_group_year=self.education_group_year
        )
        off_enrol = OfferEnrollmentFactory(offer_year=self.offer_year_calendar_deliberation.offer_year)
        self.sess_exam_dealine = SessionExamDeadlineFactory(offer_enrollment=off_enrol, deliberation_date=None,
                                                            deadline=scores_encodings_deadline._one_day_before(
                                                                self.academic_calendar_deliberation.end_date),
                                                            deadline_tutor=0,
                                                            number_session=self.nb_session)
        self.ac_score_exam_submission = AcademicCalendarFactory(
            academic_year=self.academic_year,
            reference=academic_calendar_type.SCORES_EXAM_SUBMISSION,
            start_date=self.academic_year.start_date,
            end_date=self.academic_year.end_date,
        )
        SessionExamCalendarFactory(
            academic_calendar=self.ac_score_exam_submission,
            number_session=self.nb_session
        )

    def _create_tutor_scores_submission_end_date(self, end_date):
        return OfferYearCalendarFactory(
            academic_calendar=self.ac_score_exam_submission,
            offer_year=self.off_year,
            start_date=self.academic_calendar_deliberation.start_date,
            end_date=end_date,
            education_group_year=self.education_group_year
        )

    def _get_persistent_session_exam_deadline(self):
        return SessionExamDeadline.objects.get(pk=self.sess_exam_dealine.id)

    def _change_student_deliberation_date(self, new_end_date):
        self.sess_exam_dealine.deliberation_date = new_end_date
        self.sess_exam_dealine.save()

    def _assert_date_equal(self, date1, date2):
        self.assertEqual(scores_encodings_deadline._get_date_instance(date1),
                         scores_encodings_deadline._get_date_instance(date2))

    def test_compute_deadline_wrong_reference(self):
        self.offer_year_calendar_deliberation.academic_calendar.reference = academic_calendar_type.COURSE_ENROLLMENT
        old_deadline = self.sess_exam_dealine.deadline

        self.offer_year_calendar_deliberation.save()

        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline, old_deadline)

    def test_compute_deadline_tutor_by_offer_year(self):
        """
        In this test, we will check if the tutor day delta [deadline is correctly computed]
        """
        self.offer_year_calendar_deliberation.end_date = self.offer_year_calendar_deliberation.end_date + timedelta(
            days=10)
        self.offer_year_calendar_deliberation.save()

        correct_deadlines = [0 for _ in SessionExamDeadline.objects.all()]

        OfferYearCalendarFactory(
            academic_calendar=self.ac_score_exam_submission,
            education_group_year=self.offer_year_calendar_deliberation.education_group_year,
            offer_year=self.offer_year_calendar_deliberation.offer_year
        )

        new_deadlines_tutors = [i.deadline_tutor for i in SessionExamDeadline.objects.all()]
        self.assertListEqual(new_deadlines_tutors, correct_deadlines)

    def test_get_delta_deadline_tutor(self):
        today = datetime.today()
        fourty_day_before = today - timedelta(days=40)
        self.assertEqual(40, scores_encodings_deadline._compute_delta_deadline_tutor(today, fourty_day_before))

    def test_get_delta_deadline_tutor_none_value(self):
        today = datetime.today()
        self.assertFalse(scores_encodings_deadline._compute_delta_deadline_tutor(None, None))
        self.assertFalse(scores_encodings_deadline._compute_delta_deadline_tutor(None, today))
        self.assertFalse(scores_encodings_deadline._compute_delta_deadline_tutor(today, None))

    def test_case_only_global_scores_encoding_end_date_is_set(self):
        self.offer_year_calendar_deliberation.delete()
        OfferYearCalendarFactory(academic_calendar=self.ac_score_exam_submission, start_date=None, end_date=None,
                                 offer_year=self.off_year)
        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline,
                                self.ac_score_exam_submission.end_date)
        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline_tutor_computed,
                                self.ac_score_exam_submission.end_date)

    def test_case_tutor_scores_submission_date_gt_student_deliberation_date(self):
        delibe_date = self.offer_year_calendar_deliberation.end_date - timedelta(days=10)
        self._change_student_deliberation_date(delibe_date)
        self._create_tutor_scores_submission_end_date(delibe_date + timedelta(days=5))
        self.assertEqual(self._get_persistent_session_exam_deadline().deadline_tutor_computed,
                         scores_encodings_deadline._one_day_before(delibe_date))

    def test_case_tutor_scores_submission_date_gt_offer_year_deliberation_date(self):
        offer_year_delibe_date = self.offer_year_calendar_deliberation.end_date
        self._create_tutor_scores_submission_end_date(offer_year_delibe_date + timedelta(days=5))
        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline_tutor_computed,
                                scores_encodings_deadline._one_day_before(
                                    self.offer_year_calendar_deliberation.end_date))

    def test_case_tutor_scores_submission_date_gt_scores_encodings_end_date(self):
        scores_encodings_end_date = self.ac_score_exam_submission.end_date
        self._create_tutor_scores_submission_end_date(scores_encodings_end_date + timedelta(days=5))
        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline_tutor_computed,
                                scores_encodings_deadline._one_day_before(self.ac_score_exam_submission.end_date))

    def test_case_tutor_scores_submission_date_lt_student_deliberation_date(self):
        delibe_date = self.offer_year_calendar_deliberation.end_date - timedelta(days=10)
        self._change_student_deliberation_date(delibe_date)
        off_year_cal = self._create_tutor_scores_submission_end_date(delibe_date - timedelta(days=5))
        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline_tutor_computed,
                                off_year_cal.end_date)

    def test_case_tutor_scores_submission_date_lt_offer_year_deliberation_date(self):
        off_year_delibe_date = self.offer_year_calendar_deliberation.end_date
        off_year_cal = self._create_tutor_scores_submission_end_date(off_year_delibe_date - timedelta(days=5))
        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline_tutor_computed,
                                off_year_cal.end_date)

    def test_case_tutor_scores_submission_date_lt_scores_encodings_end_date(self):
        scores_encodings_end_date = self.ac_score_exam_submission.end_date
        off_year_cal = self._create_tutor_scores_submission_end_date(scores_encodings_end_date - timedelta(days=5))
        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline_tutor_computed,
                                off_year_cal.end_date)

    def test_case_student_deliberation_date_gt_offer_year_deliberation_date(self):
        offer_year_delibe_date = self.offer_year_calendar_deliberation.end_date
        self._change_student_deliberation_date(offer_year_delibe_date + timedelta(days=5))
        before = scores_encodings_deadline._one_day_before(offer_year_delibe_date)
        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline,
                                before)

    def test_case_student_deliberation_date_lt_offer_year_deliberation_date(self):
        offer_year_delibe_date = self.offer_year_calendar_deliberation.end_date
        self._change_student_deliberation_date(offer_year_delibe_date - timedelta(days=5))
        self.assertEqual(self._get_persistent_session_exam_deadline().deadline,
                         scores_encodings_deadline._one_day_before(self.sess_exam_dealine.deliberation_date))

    def test_case_global_submission_date_lt_student_and_offer_year_delibe_date(self):
        offer_year_delibe_end_date = self.offer_year_calendar_deliberation.end_date
        self._create_tutor_scores_submission_end_date(offer_year_delibe_end_date)
        global_submission_end_date = offer_year_delibe_end_date - timedelta(days=20)
        self.ac_score_exam_submission.end_date = global_submission_end_date
        self.ac_score_exam_submission.save()
        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline, global_submission_end_date)

    def test_case_student_deliberation_date_lt_global_submission_date(self):
        new_student_delibe_date = self.ac_score_exam_submission.end_date - timedelta(days=5)
        self.sess_exam_dealine.deliberation_date = new_student_delibe_date
        self.sess_exam_dealine.save()
        self._assert_date_equal(self.sess_exam_dealine.deadline,
                                scores_encodings_deadline._one_day_before(new_student_delibe_date))

    def test_case_offer_year_deliberation_lt_global_submission_date(self):
        new_offer_year_delibe_date = self.ac_score_exam_submission.end_date - timedelta(days=5)
        self.offer_year_calendar_deliberation.end_date = new_offer_year_delibe_date
        self.offer_year_calendar_deliberation.save()
        self._assert_date_equal(self._get_persistent_session_exam_deadline().deadline,
                                scores_encodings_deadline._one_day_before(new_offer_year_delibe_date))

    def test_case_mutliple_students_offer_enrollments(self):
        students = [StudentFactory() for _ in range(10)]
        offer_enrollments = [
            OfferEnrollmentFactory(student=student, offer_year=self.offer_year_calendar_deliberation.offer_year)
            for student in students
        ]

        session_exam_deadlines = [
            SessionExamDeadlineFactory(offer_enrollment=offer_enrollment, number_session=self.nb_session,
                                       deliberation_date=self.offer_year_calendar_deliberation.end_date,
                                       deadline=scores_encodings_deadline._one_day_before(
                                           self.offer_year_calendar_deliberation.end_date),
                                       deadline_tutor=0)
            for offer_enrollment in offer_enrollments
        ]

        new_global_submission_date = self.offer_year_calendar_deliberation.end_date - timedelta(days=20)
        self.offer_year_calendar_deliberation.end_date = new_global_submission_date
        self.offer_year_calendar_deliberation.save()
        persistent_session_exams = SessionExamDeadline.objects.filter(pk__in=[obj.id for obj in session_exam_deadlines])
        for obj in persistent_session_exams:
            self._assert_date_equal(obj.deadline, scores_encodings_deadline._one_day_before(new_global_submission_date))

    def test_get_oyc_by_reference_when_education_group_year_is_null(self):
        ac_cal = AcademicCalendarFactory(reference=academic_calendar_type.DELIBERATION)
        SessionExamCalendarFactory(academic_calendar=ac_cal)
        OfferYearCalendarFactory(academic_calendar=ac_cal, education_group_year=None)
        off_year_cal_expected = OfferYearCalendarFactory(academic_calendar=ac_cal, education_group_year=None)
        oyc = scores_encodings_deadline._get_oyc_by_reference(off_year_cal_expected,
                                                              academic_calendar_type.DELIBERATION)
        self.assertEqual(oyc, off_year_cal_expected)

    def test_get_oyc_by_reference_when_no_matching_result(self):
        ac_cal = AcademicCalendarFactory(reference=academic_calendar_type.DELIBERATION)
        SessionExamCalendarFactory(academic_calendar=ac_cal)
        off_year_cal = OfferYearCalendarFactory(academic_calendar=ac_cal)
        oyc = scores_encodings_deadline._get_oyc_by_reference(off_year_cal, academic_calendar_type.COURSE_ENROLLMENT)
        self.assertIsNone(oyc)

    # ??? next 2 tests ?
    @mock.patch("assessments.business.scores_encodings_deadline.compute_deadline")
    def test_recompute_all_deadlines_when_not_impact_scores_encodings_deadlines(self, mock_compute_deadline):
        OfferYearCalendarFactory(
            academic_calendar=AcademicCalendarFactory(reference=academic_calendar_type.DELIBERATION)
        )
        self.assertFalse(mock_compute_deadline.called)

    @mock.patch("assessments.business.scores_encodings_deadline.compute_deadline")
    def test_recompute_all_deadlines_when_not_impact_scores_encodings_deadlines(self, mock_compute_deadline):
        OfferYearCalendarFactory(
            academic_calendar=AcademicCalendarFactory(reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        )
        self.assertTrue(mock_compute_deadline.called)

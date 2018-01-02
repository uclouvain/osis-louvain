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

from django.test import TestCase, Client
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base.models.exam_enrollment import ExamEnrollment

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.models.test_academic_calendar import create_academic_calendar
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from attribution.tests.factories.attribution import AttributionFactory
from base.tests.factories.session_examen import SessionExamFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.exam_enrollment import ExamEnrollmentFactory

from base.models.enums import number_session, academic_calendar_type, exam_enrollment_justification_type
from osis_common.utils.datetime import get_tzinfo

OFFER_ACRONYM = "OSIS2MA"
LEARNING_UNIT_ACRONYM = "LOSIS1211"

REGISTRATION_ID_1 = "00000001"
REGISTRATION_ID_2 = "00000002"


def _get_list_tag_and_content(messages):
    return [(m.tags, m.message) for m in messages]


class TestUploadXls(TestCase):
    def setUp(self):
        today = datetime.datetime.today()
        twenty_days = datetime.timedelta(days=20)

        #Take same academic year as the one in the associated xls file
        an_academic_year = AcademicYearFactory(year=2017)

        a_learning_unit_year = LearningUnitYearFakerFactory(academic_year=an_academic_year,
                                                            acronym=LEARNING_UNIT_ACRONYM)

        tutor = TutorFactory()

        an_academic_calendar = create_academic_calendar(an_academic_year, start_date=today - twenty_days,
                                                        end_date=today + twenty_days,
                                                        reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        SessionExamCalendarFactory(number_session=number_session.ONE,
                                   academic_calendar=an_academic_calendar)
        AttributionFactory(learning_unit_year=a_learning_unit_year,
                           tutor=tutor)
        a_session_exam = SessionExamFactory(number_session=number_session.ONE,
                                            learning_unit_year=a_learning_unit_year)

        student_1 = StudentFactory(registration_id=REGISTRATION_ID_1)
        student_2 = StudentFactory(registration_id=REGISTRATION_ID_2)

        an_offer_year = OfferYearFactory(academic_year=an_academic_year,
                                         acronym=OFFER_ACRONYM)
        offer_enrollment_1 = OfferEnrollmentFactory(offer_year=an_offer_year,
                                                    student=student_1)
        offer_enrollment_2 = OfferEnrollmentFactory(offer_year=an_offer_year,
                                                    student=student_2)

        learning_unit_enrollment_1 = LearningUnitEnrollmentFactory(learning_unit_year=a_learning_unit_year,
                                                                   offer_enrollment=offer_enrollment_1)
        learning_unit_enrollment_2 = LearningUnitEnrollmentFactory(learning_unit_year=a_learning_unit_year,
                                                                   offer_enrollment=offer_enrollment_2)

        ExamEnrollmentFactory(session_exam=a_session_exam,
                              learning_unit_enrollment=learning_unit_enrollment_1)
        ExamEnrollmentFactory(session_exam=a_session_exam,
                              learning_unit_enrollment=learning_unit_enrollment_2)

        user = tutor.person.user
        self.client = Client()
        self.client.force_login(user=user)
        self.url = reverse('upload_encoding', kwargs={'learning_unit_year_id': a_learning_unit_year.id})

    def test_with_no_file_uploaded(self):
        response = self.client.post(self.url, {'file': ''}, follow=True)
        messages = list(response.context['messages'])

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(messages[0].message, _('no_file_submitted'))

    def test_with_incorrect_format_file(self):
        with open("assessments/tests/resources/bad_format.txt", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].tags, 'error')
            self.assertEqual(messages[0].message, _('file_must_be_xlsx'))

    def test_with_no_scores_encoded(self):
        with open("assessments/tests/resources/empty_scores.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].tags, 'error')
            self.assertEqual(messages[0].message, _('no_score_injected'))

    def test_with_incorrect_justification(self):
        INCORRECT_LINES = '13'
        with open("assessments/tests/resources/incorrect_justification.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('error', "%s : %s %s" % (_('justification_invalid_value'), _('Line'), INCORRECT_LINES)),
                          messages_tag_and_content)

    def test_with_numbers_outside_scope(self):
        INCORRECT_LINES = '12, 13'
        with open("assessments/tests/resources/incorrect_scores.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('error', "%s : %s %s" % (_('scores_must_be_between_0_and_20'), _('Line'), INCORRECT_LINES)),
                          messages_tag_and_content)

    def test_with_correct_score_sheet(self):
        NUMBER_CORRECT_SCORES = "2"
        SCORE_1 = 16
        SCORE_2 = exam_enrollment_justification_type.ABSENCE_UNJUSTIFIED
        with open("assessments/tests/resources/correct_score_sheet.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('success', '%s %s' % (NUMBER_CORRECT_SCORES, _('score_saved'))),
                          messages_tag_and_content)

            exam_enrollment_1 = ExamEnrollment.objects.get(
                learning_unit_enrollment__offer_enrollment__student__registration_id=REGISTRATION_ID_1
            )
            self.assertEqual(exam_enrollment_1.score_draft, SCORE_1)

            exam_enrollment_2 = ExamEnrollment.objects.get(
                learning_unit_enrollment__offer_enrollment__student__registration_id=REGISTRATION_ID_2
            )
            self.assertEqual(exam_enrollment_2.justification_draft, SCORE_2)

    def test_with_formula(self):
        NUMBER_SCORES = "2"
        SCORE_1 = 15
        SCORE_2 = 17
        with open("assessments/tests/resources/score_sheet_with_formula.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('success', '%s %s' % (NUMBER_SCORES, _('score_saved'))),
                          messages_tag_and_content)

            exam_enrollment_1 = ExamEnrollment.objects.get(
                learning_unit_enrollment__offer_enrollment__student__registration_id=REGISTRATION_ID_1
            )
            self.assertEqual(exam_enrollment_1.score_draft, SCORE_1)

            exam_enrollment_2 = ExamEnrollment.objects.get(
                learning_unit_enrollment__offer_enrollment__student__registration_id=REGISTRATION_ID_2
            )
            self.assertEqual(exam_enrollment_2.score_draft, SCORE_2)

    def test_with_incorrect_formula(self):
        NUMBER_CORRECT_SCORES = "1"
        INCORRECT_LINE = "13"
        SCORE_1 = 15
        with open("assessments/tests/resources/incorrect_formula.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('error', "%s : %s %s" % (_('scores_must_be_between_0_and_20'), _('Line'), INCORRECT_LINE)),
                          messages_tag_and_content)
            self.assertIn(('success', '%s %s' % (NUMBER_CORRECT_SCORES, _('score_saved'))),
                          messages_tag_and_content)
            exam_enrollment_1 = ExamEnrollment.objects.get(
                learning_unit_enrollment__offer_enrollment__student__registration_id=REGISTRATION_ID_1
            )
            self.assertEqual(exam_enrollment_1.score_draft, SCORE_1)


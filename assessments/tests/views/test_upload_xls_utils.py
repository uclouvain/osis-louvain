##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

from django.contrib.auth.models import Group
from django.http import Http404
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base.tests.factories.academic_calendar import AcademicCalendarFactory

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from attribution.tests.factories.attribution import AttributionFactory
from base.tests.factories.session_examen import SessionExamFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.exam_enrollment import ExamEnrollmentFactory

from base.models.enums import number_session, academic_calendar_type, exam_enrollment_justification_type
from base.tests.mixin.academic_year import AcademicYearMockMixin

OFFER_ACRONYM = "OSIS2MA"
LEARNING_UNIT_ACRONYM = "LOSIS1211"

REGISTRATION_ID_1 = "00000001"
REGISTRATION_ID_2 = "00000002"

EMAIL_1 = "adam.smith@test.be"
EMAIL_2 = "john.doe@test.be"


def _get_list_tag_and_content(messages):
    return [(m.tags, m.message) for m in messages]


def generate_exam_enrollments(year, with_different_offer=False):
    number_enrollments = 2
    academic_year = AcademicYearFactory(year=year)

    an_academic_calendar = AcademicCalendarFactory(academic_year=academic_year,
                                                   start_date=datetime.datetime.today() - datetime.timedelta(days=20),
                                                   end_date=datetime.datetime.today() + datetime.timedelta(days=20),
                                                   reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
    session_exam_calendar = SessionExamCalendarFactory(number_session=number_session.ONE,
                                                       academic_calendar=an_academic_calendar)

    learning_unit_year = LearningUnitYearFakerFactory(academic_year=academic_year,
                                                      learning_container_year__academic_year=academic_year,
                                                      acronym=LEARNING_UNIT_ACRONYM)
    attribution = AttributionFactory(learning_unit_year=learning_unit_year)

    if with_different_offer:
        session_exams = [SessionExamFactory(number_session=number_session.ONE, learning_unit_year=learning_unit_year,
                                            offer_year__academic_year=academic_year)
                         for _ in range(0, number_enrollments)]
    else:
        session_exams = [SessionExamFactory(number_session=number_session.ONE, learning_unit_year=learning_unit_year,
                                            offer_year__academic_year=academic_year)] * number_enrollments
    offer_years = [session_exam.offer_year for session_exam in session_exams]

    exam_enrollments = list()
    for i in range(0, number_enrollments):
        student = StudentFactory()
        offer_enrollment = OfferEnrollmentFactory(offer_year=offer_years[i], student=student)
        learning_unit_enrollment = LearningUnitEnrollmentFactory(learning_unit_year=learning_unit_year,
                                                                 offer_enrollment=offer_enrollment)
        exam_enrollments.append(ExamEnrollmentFactory(session_exam=session_exams[i],
                                                      learning_unit_enrollment=learning_unit_enrollment))
    return locals()


class MixinTestUploadScoresFile(AcademicYearMockMixin):
    def setUp(self):
        Group.objects.get_or_create(name="tutors")
        data = generate_exam_enrollments(2017)
        self.academic_year = data["academic_year"]
        self.exam_enrollments = data["exam_enrollments"]
        self.attribution = data["attribution"]
        self.learning_unit_year = data["learning_unit_year"]
        self.offer_year = data["offer_years"][0]
        self.students = [enrollment.learning_unit_enrollment.offer_enrollment.student for enrollment
                         in self.exam_enrollments]

        self.offer_year.acronym = OFFER_ACRONYM
        self.offer_year.save()

        registration_ids = [REGISTRATION_ID_1, REGISTRATION_ID_2]
        mails = [EMAIL_1, EMAIL_2]
        data_to_modify_for_students = list(zip(registration_ids, mails))
        for i in range(0, 2):
            registration_id, email = data_to_modify_for_students[i]
            student = self.students[i]
            student.registration_id = registration_id
            student.save()
            student.person.email = email
            student.person.save()

        self.client = Client()
        self.client.force_login(user=self.attribution.tutor.person.user)
        self.url = reverse('upload_encoding', kwargs={'learning_unit_year_id': self.learning_unit_year.id})

        # Mock academic_year in order to be decouple from system time
        self.mock_academic_year(
            current_academic_year=self.academic_year,
            starting_academic_year=self.academic_year
        )

    def assert_enrollments_equal(self, exam_enrollments, attribute_value_list):
        [enrollment.refresh_from_db() for enrollment in exam_enrollments]
        data = zip(exam_enrollments, attribute_value_list)
        for exam_enrollment, tuple_attribute_value in data:
            attribute, value = tuple_attribute_value
            self.assertEqual(getattr(exam_enrollment, attribute), value)


class TestTransactionNonAtomicUploadXls(MixinTestUploadScoresFile, TransactionTestCase):
    @mock.patch("assessments.views.upload_xls_utils._show_error_messages", side_effect=Http404)
    def test_when_exception_occured_after_saving_scores(self, mock_method_that_raise_exception):
        SCORE_1 = 16
        SCORE_2 = exam_enrollment_justification_type.ABSENCE_UNJUSTIFIED
        with open("assessments/tests/resources/correct_score_sheet.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            self.assertTrue(mock_method_that_raise_exception.called)
            self.assert_enrollments_equal(
                self.exam_enrollments,
                [("score_draft", SCORE_1), ("justification_draft", SCORE_2)]
            )


class TestUploadXls(MixinTestUploadScoresFile, TestCase):
    def test_with_no_file_uploaded(self):
        response = self.client.post(self.url, {'file': ''}, follow=True)
        messages = list(response.context['messages'])

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, 'error')
        self.assertEqual(messages[0].message, _('You have to select a file to upload.'))

    def test_with_incorrect_format_file(self):
        with open("assessments/tests/resources/bad_format.txt", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].tags, 'error')
            self.assertEqual(messages[0].message, _("The file must be a valid 'XLSX' excel file"))

    def test_with_no_scores_encoded(self):
        with open("assessments/tests/resources/empty_scores.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].tags, 'error')
            self.assertEqual(messages[0].message, _('No score injected'))

    def test_with_incorrect_justification(self):
        INCORRECT_LINES = '13'
        with open("assessments/tests/resources/incorrect_justification.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('error', "%s : %s %s" % (_('Invalid justification value'), _('Row'), INCORRECT_LINES)),
                          messages_tag_and_content)

    def test_with_numbers_outside_scope(self):
        INCORRECT_LINES = '12, 13'
        with open("assessments/tests/resources/incorrect_scores.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('error', "%s : %s %s" % (_("Scores must be between 0 and 20"), _('Row'), INCORRECT_LINES)),
                          messages_tag_and_content)

    def test_with_correct_score_sheet(self):
        NUMBER_CORRECT_SCORES = "2"
        SCORE_1 = 16
        SCORE_2 = exam_enrollment_justification_type.ABSENCE_UNJUSTIFIED
        with open("assessments/tests/resources/correct_score_sheet.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('success', '%s %s' % (NUMBER_CORRECT_SCORES, _('Score saved'))),
                          messages_tag_and_content)

            self.assert_enrollments_equal(
                self.exam_enrollments,
                [("score_draft", SCORE_1), ("justification_draft", SCORE_2)]
            )

    def test_with_formula(self):
        NUMBER_SCORES = "2"
        with open("assessments/tests/resources/score_sheet_with_formula.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('success', '%s %s' % (NUMBER_SCORES, _('Score saved'))),
                          messages_tag_and_content)

            self.assert_enrollments_equal(
                self.exam_enrollments,
                [("score_draft", 15), ("score_draft", 17)]
            )

    def test_with_incorrect_formula(self):
        NUMBER_CORRECT_SCORES = "1"
        INCORRECT_LINE = "13"
        with open("assessments/tests/resources/incorrect_formula.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('error', "%s : %s %s" % (_("Scores must be between 0 and 20"), _('Row'), INCORRECT_LINE)),
                          messages_tag_and_content)
            self.assertIn(('success', '%s %s' % (NUMBER_CORRECT_SCORES, _('Score saved'))),
                          messages_tag_and_content)

            self.assert_enrollments_equal(
                self.exam_enrollments[:1],
                [("score_draft", 15)]
            )

    def test_with_registration_id_not_matching_email(self):
        INCORRECT_LINES = '12, 13'
        with open("assessments/tests/resources/registration_id_not_matching_email.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('error', "%s : %s %s" % (_('Registration ID does not match email'),
                                                    _('Row'),
                                                    INCORRECT_LINES)),
                          messages_tag_and_content)

    def test_with_correct_score_sheet_white_spaces_around_emails(self):
        NUMBER_CORRECT_SCORES = "2"
        with open("assessments/tests/resources/correct_score_sheet_spaces_around_emails.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('success', '%s %s' % (NUMBER_CORRECT_SCORES, _('Score saved'))),
                          messages_tag_and_content)

            self.assert_enrollments_equal(
                self.exam_enrollments,
                [("score_draft", 16), ("justification_draft", exam_enrollment_justification_type.ABSENCE_UNJUSTIFIED)]
            )

    def test_with_correct_score_sheet_white_one_empty_email(self):
        self.students[0].person.email = None
        self.students[0].person.save()
        NUMBER_CORRECT_SCORES = "2"
        with open("assessments/tests/resources/correct_score_sheet_one_empty_email.xlsx", 'rb') as score_sheet:
            response = self.client.post(self.url, {'file': score_sheet}, follow=True)
            messages = list(response.context['messages'])

            messages_tag_and_content = _get_list_tag_and_content(messages)
            self.assertIn(('success', '%s %s' % (NUMBER_CORRECT_SCORES, _('Score saved'))),
                          messages_tag_and_content)

            self.assert_enrollments_equal(
                self.exam_enrollments,
                [("score_draft", 16), ("justification_draft", exam_enrollment_justification_type.ABSENCE_UNJUSTIFIED)]
            )

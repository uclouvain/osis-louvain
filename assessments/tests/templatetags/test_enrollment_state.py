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

from django.test import TestCase

from assessments.templatetags.enrollment_state import enrolled_exists
from base.models.enums import exam_enrollment_state as enrollment_states
from base.models.enums import number_session
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.exam_enrollment import ExamEnrollmentFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.session_examen import SessionExamFactory


class EnrollmentTests(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory(current=True)
        self.session_exam_calendar = SessionExamCalendarFactory(academic_calendar__academic_year=self.academic_year,
                                                                number_session=number_session.ONE)
        self.session_exam = SessionExamFactory(number_session=number_session.ONE,
                                               learning_unit_year__academic_year=self.academic_year)

    def test_not_enrolled_exam_exists(self):
        exam_enrollment = ExamEnrollmentFactory(session_exam=self.session_exam,
                                                enrollment_state=enrollment_states.NOT_ENROLLED)

        self.assertFalse(enrolled_exists([exam_enrollment]))

    def test_enrolled_exam_exists(self):
        exam_enrollment = ExamEnrollmentFactory(session_exam=self.session_exam,
                                                enrollment_state=enrollment_states.ENROLLED)

        self.assertTrue(enrolled_exists([exam_enrollment]))

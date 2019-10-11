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
from unittest import mock

from django.test import TestCase

from base.signals.publisher import compute_student_score_encoding_deadline
from base.tests.factories.session_exam_deadline import SessionExamDeadlineFactory


class SessionExamDeadlineTest(TestCase):

    def setUp(self):
        self.sess_exam_deadline = SessionExamDeadlineFactory()

    def test_compute_deadline_is_called_case_changing_student_deliberation_date(self):
        with mock.patch.object(compute_student_score_encoding_deadline, 'send') as mock_method:
            self.sess_exam_deadline.deadline_tutor = 5 # Changing a different field from deliberation_date
            self.sess_exam_deadline.save()
            self.assertTrue(not mock_method.called)

            self.sess_exam_deadline.deliberation_date = datetime.datetime.now()
            self.sess_exam_deadline.save()
            self.assertTrue(mock_method.called)

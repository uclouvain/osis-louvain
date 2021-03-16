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
from faker import Faker

from base.models import academic_calendar
from base.models.exceptions import StartDateHigherThanEndDateException
from base.signals.publisher import compute_all_scores_encodings_deadlines
from base.tests.factories.academic_calendar import AcademicCalendarFactory, OpenAcademicCalendarFactory, \
    CloseAcademicCalendarFactory


class AcademicCalendarTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        fake = Faker()
        cls.future_date = fake.future_date()
        cls.past_date = fake.past_date()

    def test_start_date_higher_than_end_date(self):
        with self.assertRaises(StartDateHigherThanEndDateException):
            AcademicCalendarFactory(start_date=self.future_date, end_date=self.past_date)

    def test_find_highlight_academic_calendar(self):
        open_academic_calendar = OpenAcademicCalendarFactory()
        CloseAcademicCalendarFactory()
        OpenAcademicCalendarFactory(highlight_description=None)
        OpenAcademicCalendarFactory(highlight_title="")

        self.assertQuerysetEqual(
            academic_calendar.find_highlight_academic_calendar(),
            [open_academic_calendar],
            transform=lambda rec: rec
        )

    def test_compute_deadline_is_called_case_academic_calendar_save(self):
        with mock.patch.object(compute_all_scores_encodings_deadlines, 'send') as mock_method:
            AcademicCalendarFactory()
            self.assertTrue(mock_method.called)

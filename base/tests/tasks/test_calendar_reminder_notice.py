# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import datetime
import attr

import mock
import numpy as np
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, SimpleTestCase, override_settings

from base.business.academic_calendar import AcademicEvent
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tasks import calendar_reminder_notice


class TestGetAcademicEventsToRemind(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.open_event = AcademicEvent(
            id=1,
            title="Candidature en ligne",
            authorized_target_year=2020,
            start_date=datetime.date.today() - datetime.timedelta(days=5),
            end_date=datetime.date.today() + datetime.timedelta(days=5),
            type=AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name
        )

    def setUp(self) -> None:
        self.patcher_get_academic_events = mock.patch(
            'base.views.academic_calendar.read.AcademicEventRepository.get_academic_events'
        )
        self.mock_get_academic_events = self.patcher_get_academic_events.start()
        self.mock_get_academic_events.return_value = [self.open_event]
        self.addCleanup(self.patcher_get_academic_events.stop)

    @mock.patch('base.tasks.calendar_reminder_notice._is_due_date_reached', return_value=True)
    def test_get_academic_events_to_remind_assert_return_list_events(self, mock_is_due_date):
        expected_result = [self.open_event]

        self.assertListEqual(
            calendar_reminder_notice._get_academic_events_to_remind(
                (AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name,)
            ),
            expected_result
        )

    @mock.patch('base.tasks.calendar_reminder_notice._is_due_date_reached', return_value=False)
    def test_get_academic_events_to_remind_assert_return_empty_list_events(self, mock_is_due_date):
        expected_result = []

        self.assertListEqual(
            calendar_reminder_notice._get_academic_events_to_remind(
                (AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name,)
            ),
            expected_result
        )


class TestIsDueDateReached(SimpleTestCase):
    def setUp(self) -> None:
        self.academic_event = AcademicEvent(
            id=1,
            title="Candidature en ligne",
            authorized_target_year=2020,
            start_date=datetime.date.today() - datetime.timedelta(days=5),
            end_date=datetime.date.today() + datetime.timedelta(days=5),
            type=AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name
        )

    def test_is_due_date_reached_case_5_working_days_left(self):
        five_workings_days = np.busday_offset(datetime.date.today(), 5)
        self.academic_event = attr.evolve(self.academic_event, start_date=five_workings_days)

        self.assertTrue(calendar_reminder_notice._is_due_date_reached(self.academic_event))

    def test_is_due_date_reached_case_1_working_days_left(self):
        one_workings_days = np.busday_offset(datetime.date.today(), 1)
        self.academic_event = attr.evolve(self.academic_event, start_date=one_workings_days)

        self.assertTrue(calendar_reminder_notice._is_due_date_reached(self.academic_event))

    def test_is_due_date_reached_case_2_working_days_left(self):
        two_workings_days = np.busday_offset(datetime.date.today(), 2)
        self.academic_event = attr.evolve(self.academic_event, start_date=two_workings_days)

        self.assertFalse(calendar_reminder_notice._is_due_date_reached(self.academic_event))


class TestSendReminderMail(SimpleTestCase):
    def setUp(self) -> None:
        self.academic_event = AcademicEvent(
            id=1,
            title="Candidature en ligne",
            authorized_target_year=2020,
            start_date=datetime.date.today() - datetime.timedelta(days=5),
            end_date=datetime.date.today() + datetime.timedelta(days=5),
            type=AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name
        )
        self.receiver_emails = ['dummy@gmail.com']

    @mock.patch('base.tasks.calendar_reminder_notice.message_service.send_messages')
    def test_assert_call_message_service(self, mock_send_messages):
        calendar_reminder_notice._send_reminder_mail(self.receiver_emails, [self.academic_event])
        self.assertTrue(mock_send_messages.called)


class TestRunCalendarReminderNotice(SimpleTestCase):
    @override_settings(ACADEMIC_CALENDAR_REMINDER_EMAILS='')
    def test_missing_settings_assert_raise_exception(self):
        with self.assertRaises(ImproperlyConfigured):
            calendar_reminder_notice.run()

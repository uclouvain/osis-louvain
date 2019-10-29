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
import datetime
from unittest.mock import Mock

from django.test import TestCase

from base.middlewares import notification_middleware
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.user import UserFactory


class TestSendAcademicCalendarNotifications(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.today = datetime.date.today()
        cls.academic_calendar_today = AcademicCalendarFactory(start_date=cls.today,
                                                              end_date=cls.today)
        cls.academic_calendar_in_1_week = AcademicCalendarFactory(start_date=cls.today+datetime.timedelta(weeks=1),
                                                                  end_date=cls.today+datetime.timedelta(weeks=1))
        cls.academic_calendar_in_3_weeks = AcademicCalendarFactory(start_date=cls.today + datetime.timedelta(weeks=3),
                                                                   end_date=cls.today + datetime.timedelta(weeks=3))

    def setUp(self):
        self.method_set = notification_middleware.set_notifications_last_read_as_now_for_user
        self.method_get = notification_middleware.get_notifications_last_time_read_for_user

        notification_middleware.set_notifications_last_read_as_now_for_user = Mock()
        notification_middleware.get_notifications_last_time_read_for_user = Mock()

    def tearDown(self):
        notification_middleware.set_notifications_last_read_as_now_for_user = self.method_set
        notification_middleware.get_notifications_last_time_read_for_user = self.method_get

    def test_create_no_notifications_if_date_last_read_is_today(self):
        notification_middleware.get_notifications_last_time_read_for_user.return_value = self.today
        notification_middleware.send_academic_calendar_notifications(self.user)

        self.assertQuerysetEqual(self.user.notifications.unread(), [])
        notification_middleware.set_notifications_last_read_as_now_for_user.assert_called_once_with(self.user)
        notification_middleware.get_notifications_last_time_read_for_user.assert_called_once_with(self.user)

    def test_create_notifications_of_academic_calendar_events_within_2_weeks_if_no_last_read(self):
        notification_middleware.get_notifications_last_time_read_for_user.return_value = None
        notification_middleware.send_academic_calendar_notifications(self.user)

        self.assertCountEqual(
            [notif.verb for notif in self.user.notifications.unread()],
            [str(self.academic_calendar_today), str(self.academic_calendar_in_1_week)]
        )

        notification_middleware.set_notifications_last_read_as_now_for_user.assert_called_once_with(self.user)
        notification_middleware.get_notifications_last_time_read_for_user.assert_called_once_with(self.user)

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

from base.tests.factories.notifications import NotificationFactory
from base.tests.factories.user import UserFactory
from base.utils.cache import cache
from base.utils.notifications import clear_user_notifications, \
    get_user_notifications, mark_notifications_as_read, get_user_unread_notifications, get_user_read_notifications


class TestNotificationsBaseClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_without_notifications = UserFactory()
        cls.user_with_notifications = UserFactory()

        cls.unread_notifications = [NotificationFactory(recipient=cls.user_with_notifications) for _ in range(5)]
        cls.read_notifications = [NotificationFactory(recipient=cls.user_with_notifications, unread=False)
                                  for _ in range(3)]
        cls.all_notifications = cls.unread_notifications + cls.read_notifications

    def tearDown(self):
        cache.clear()

    @staticmethod
    def transform_method(obj):
        return obj

    def assert_queryset_equal(self, qs, values):
        return self.assertQuerysetEqual(qs, values, transform=self.transform_method, ordered=False)


class TestGetUserNotifications(TestNotificationsBaseClass):
    def test_should_return_empty_list_when_user_has_no_notifications(self):
        self.assert_queryset_equal(get_user_notifications(self.user_without_notifications),
                                   [])

    def test_should_return_unread_first_then_read_notifications_when_user_got_notifications(self):
        returned_notifications = get_user_notifications(self.user_with_notifications)
        self.assert_queryset_equal(returned_notifications,
                                   self.all_notifications)
        self.assertCountEqual(returned_notifications[:5],
                              self.unread_notifications)


class TestClearNotifications(TestNotificationsBaseClass):
    def test_user_should_have_no_notifications_after_clear(self):
        self.assert_queryset_equal(get_user_notifications(self.user_with_notifications),
                                   self.all_notifications)

        clear_user_notifications(self.user_with_notifications)

        self.assert_queryset_equal(get_user_notifications(self.user_with_notifications),
                                   [])


class TestMarkNotificationsAsRead(TestNotificationsBaseClass):
    def test_all_notifications_should_be_read_after_method_call(self):
        self.assert_queryset_equal(
            get_user_unread_notifications(self.user_with_notifications),
            self.unread_notifications
        )
        self.assert_queryset_equal(
            get_user_read_notifications(self.user_with_notifications),
            self.read_notifications
        )

        mark_notifications_as_read(self.user_with_notifications)

        self.assert_queryset_equal(
            get_user_unread_notifications(self.user_with_notifications),
            []
        )
        self.assert_queryset_equal(
            get_user_read_notifications(self.user_with_notifications),
            list(self.user_with_notifications.notifications.all())
        )

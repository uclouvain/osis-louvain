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
from unittest import mock

from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.user import UserFactory


class TestNotificationsViewMixin:
    def test_user_must_be_logged(self):
        self.client.logout()
        response = self.client.post(self.url, data={})
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_request_must_be_an_ajax_one(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_request_must_be_a_post(self):
        response = self.client.get(self.url, {},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)


class TestClearUserNotifications(TestCase, TestNotificationsViewMixin):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse("clear_notifications")

    def setUp(self):
        self.client.force_login(self.user)

    def test_make_call_to_clear_notifications_method(self):
        from base.utils import notifications
        real_method = notifications.clear_user_notifications

        notifications.clear_user_notifications = mock.MagicMock()
        response = self.client.post(self.url, {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, HttpResponse.status_code)
        notifications.clear_user_notifications.assert_called_once_with(self.user)

        notifications.clear_user_notifications = real_method


class TestMarkNotificationsAsRead(TestCase, TestNotificationsViewMixin):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.url = reverse("mark_notifications_as_read")

    def setUp(self):
        self.client.force_login(self.user)

    def test_make_call_to_mark_notifications_as_read_method(self):
        from base.utils import notifications
        real_method = notifications.mark_notifications_as_read

        notifications.mark_notifications_as_read = mock.MagicMock()
        response = self.client.post(self.url, {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, HttpResponse.status_code)
        notifications.mark_notifications_as_read.assert_called_once_with(self.user)

        notifications.mark_notifications_as_read = real_method

# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

from django import urls, http
from django.utils.translation import gettext_lazy as _
from django.test import TestCase

from base.tests.factories.person import PersonFactory
from program_management.ddd import command


class TestCopyToCache(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = urls.reverse("copy_element")
        cls.person = PersonFactory()

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

    def test_should_raise_http_response_not_allowed_when_view_is_called_via_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HttpResponseNotAllowed.status_code)

    @mock.patch("program_management.ddd.service.write.copy_element_service.copy_element_service")
    def test_should_call_copy_element_service_when_view_is_called_via_post_request(self, mock_copy_service):
        response = self.client.post(self.url, data={
            "element_code": "LOSIS2548",
            "element_year": 2015,
        })
        copy_command = command.CopyElementCommand(self.person.user.id, "LOSIS2548", 2015)
        mock_copy_service.assert_called_with(copy_command)
        self.assertEqual(
            response.json(),
            {"success_message": "<strong>{clipboard_title}</strong><br>{object_str}".format(
                clipboard_title=_("Copied element"),
                object_str="LOSIS2548 - 2015"
            )}
        )


class TestCutToCache(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = urls.reverse("cut_element")
        cls.person = PersonFactory()

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

    def test_should_raise_http_response_not_allowed_when_view_is_called_via_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HttpResponseNotAllowed.status_code)

    @mock.patch("program_management.ddd.service.write.cut_element_service.cut_element_service")
    def test_should_call_copy_element_service_when_view_is_called_via_post_request(self, mock_cut_service):
        response = self.client.post(self.url, data={
            "element_code": "WMD200M",
            "element_year": 2021,
            "path_to_detach": "DROI2033M|WMD199M",
        })
        copy_command = command.CutElementCommand(self.person.user.id, "WMD200M", 2021, "DROI2033M|WMD199M")
        mock_cut_service.assert_called_with(copy_command)
        self.assertEqual(
            response.json(),
            {"success_message": "<strong>{clipboard_title}</strong><br>{object_str}".format(
                clipboard_title=_("Cut element"),
                object_str="WMD200M - 2021"
            )}
        )


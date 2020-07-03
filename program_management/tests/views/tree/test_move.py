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

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

from base.tests.factories.person import CentralManagerForUEFactory
from program_management.ddd.domain import node
from program_management.tests.ddd.factories.commands.order_down_link_command import OrderDownLinkCommandFactory
from program_management.tests.ddd.factories.commands.order_up_link_command import OrderUpLinkCommandFactory
from program_management.tests.factories.element import ElementGroupYearFactory


@override_flag('education_group_update', active=True)
class TestUp(TestCase):
    def setUp(self):
        self.person = CentralManagerForUEFactory()
        element_group_year = ElementGroupYearFactory()
        self.url = reverse("content_up")
        self.path = "19774|{}|789".format(element_group_year.id)
        self.post_valid_data = {"path": self.path}
        self.client.force_login(self.person.user)

    @mock.patch("program_management.ddd.service.write.up_link_service.up_link")
    @mock.patch.object(User, "has_perms", return_value=True)
    def test_up_case_success(self, mock_permission, mock_up):
        mock_up.return_value = node.NodeIdentity(code="CODE", year=2020)
        http_referer = reverse('home')

        response = self.client.post(self.url, data=self.post_valid_data, HTTP_REFERER=http_referer)
        self.assertRedirects(response, http_referer)

        mock_up.assert_called_with(OrderUpLinkCommandFactory(path=self.path))


@override_flag('education_group_update', active=True)
class TestDown(TestCase):
    def setUp(self):
        self.person = CentralManagerForUEFactory()
        element_group_year = ElementGroupYearFactory()
        self.url = reverse("content_down")
        self.path = "19774|{}|789".format(element_group_year.id)
        self.post_valid_data = {"path": self.path}
        self.client.force_login(self.person.user)

    @mock.patch("program_management.ddd.service.write.down_link_service.down_link")
    @mock.patch.object(User, "has_perms", return_value=True)
    def test_down_case_success(self, mock_permission, mock_down):
        mock_down.return_value = node.NodeIdentity(code="CODE", year=2020)
        http_referer = reverse('home')

        response = self.client.post(self.url, data=self.post_valid_data, HTTP_REFERER=http_referer)
        self.assertRedirects(response, http_referer)

        mock_down.assert_called_with(OrderDownLinkCommandFactory(path=self.path))

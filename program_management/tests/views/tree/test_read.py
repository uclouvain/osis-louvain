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
import mock
from django.http import HttpResponseNotAllowed, HttpResponseBadRequest, JsonResponse
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.person import PersonFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestTreeJsonView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("tree_json", kwargs={'root_id': 15})
        cls.person = PersonFactory()

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

    def test_when_not_logged(self):
        self.client.logout()

        response = self.client.get(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_with_permission_post_method(self):
        response = self.client.post(self.url)

        self.assertTemplateUsed(response, "method_not_allowed.html")
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    def test_user_with_permission_get_method_not_ajax(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)

    @mock.patch('program_management.views.tree.read.node_identity_service.get_node_identity_from_element_id')
    @mock.patch('program_management.views.tree.read.get_program_tree_service.get_program_tree')
    def test_user_with_permission_get_method_ajax(self, mock_get_program_tree, mock_get_node_id):
        mock_get_program_tree.return_value = ProgramTreeFactory()

        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, JsonResponse.status_code)

        self.assertTrue(mock_get_program_tree.called)
        self.assertTrue(mock_get_node_id.called)

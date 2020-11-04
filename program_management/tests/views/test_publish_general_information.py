##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.person import PersonWithPermissionsFactory
from program_management.ddd.service.write.publish_program_trees_using_node_service import PublishNodesException
from program_management.ddd.domain.node import NodeIdentity
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class GeneralInformationPublishViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.program_tree = ProgramTreeFactory()

        cls.url = reverse('publish_general_information', kwargs={
            'code': cls.program_tree.root_node.code,
            'year': cls.program_tree.root_node.year
        })
        cls.person = PersonWithPermissionsFactory('view_educationgroup')

    def setUp(self):
        self.get_program_tree_patcher = mock.patch(
            "program_management.views.publish_general_information.get_program_tree_service.get_program_tree",
            return_value=self.program_tree
        )
        self.mocked_get_program_tree = self.get_program_tree_patcher.start()
        self.addCleanup(self.get_program_tree_patcher.stop)

        self.client.force_login(self.person.user)

    def test_publish_case_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_public_case_methods_not_allowed(self):
        methods_not_allowed = ['get', 'delete', 'put']
        for method in methods_not_allowed:
            request_to_call = getattr(self.client, method)
            response = request_to_call(self.url)
            self.assertEqual(response.status_code, 405)

    @mock.patch("program_management.views.publish_general_information."
                "publish_program_trees_using_node_service.publish_program_trees_using_node",
                side_effect=lambda e: True)
    def test_publish_case_ok_redirection_with_success_message(self, mock_publish):
        response = self.client.post(self.url)

        msg = [m.message for m in messages.get_messages(response.wsgi_request)]
        msg_level = [m.level for m in messages.get_messages(response.wsgi_request)]

        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    @mock.patch("program_management.views.publish_general_information."
                "publish_program_trees_using_node_service.publish_program_trees_using_node",
                side_effect=PublishNodesException([NodeIdentity(code='LDROI100', year=2018)]))
    def test_publish_case_ko_redirection_with_error_message(self, mock_publish):
        response = self.client.post(self.url)

        msg = [m.message for m in messages.get_messages(response.wsgi_request)]
        msg_level = [m.level for m in messages.get_messages(response.wsgi_request)]

        self.assertEqual(len(msg), 1)
        self.assertIn(messages.ERROR, msg_level)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

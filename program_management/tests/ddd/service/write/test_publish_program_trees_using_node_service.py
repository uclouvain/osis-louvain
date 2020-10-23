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

from django.http import HttpResponse
from django.test import TestCase

from base.models.enums.education_group_types import TrainingType, MiniTrainingType
from program_management.ddd import command
from program_management.ddd.service.write import publish_program_trees_using_node_service
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestPublishProgramTreesUsingNodeService(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.program_tree = ProgramTreeFactory()

        cls.cmd = command.PublishProgramTreesVersionUsingNodeCommand(
            code=cls.program_tree.root_node.code,
            year=cls.program_tree.root_node.year
        )

    def setUp(self):
        self.get_pgrm_trees_patcher = mock.patch(
            "program_management.ddd.service.write.publish_program_trees_using_node_service."
            "search_program_trees_using_node_service.search_program_trees_using_node",
            return_value=[self.program_tree]
        )
        self.mocked_get_pgrm_trees = self.get_pgrm_trees_patcher.start()
        self.addCleanup(self.get_pgrm_trees_patcher.stop)

        self.get_publish_url_patcher = mock.patch(
            "program_management.ddd.service.write.publish_program_trees_using_node_service."
            "GetNodePublishUrl.get_url_from_node",
            return_value="dummy-url"
        )
        self.mocked_get_publish_url = self.get_publish_url_patcher.start()
        self.addCleanup(self.get_publish_url_patcher.stop)

    @mock.patch('requests.get', return_value=HttpResponse)
    @mock.patch('threading.Thread')
    def test_publish_call_seperate_thread(self, mock_thread, mock_requests_get):
        mock_thread.start.return_value = True
        publish_program_trees_using_node_service.publish_program_trees_using_node(self.cmd)
        self.assertTrue(mock_thread.start)


class TestBulkPublish(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.minor = NodeGroupYearFactory(node_type=MiniTrainingType.ACCESS_MINOR)
        cls.deepening = NodeGroupYearFactory(node_type=MiniTrainingType.DEEPENING)
        cls.major = NodeGroupYearFactory(node_type=MiniTrainingType.FSA_SPECIALITY)
        cls.training = NodeGroupYearFactory(node_type=TrainingType.PGRM_MASTER_120)

    def setUp(self):
        self.requests_get_patcher = mock.patch('requests.get', return_value=HttpResponse)
        self.mocked_requests_get = self.requests_get_patcher.start()
        self.addCleanup(self.requests_get_patcher.stop)

        self.get_publish_url_patcher = mock.patch(
            "program_management.ddd.service.write.publish_program_trees_using_node_service."
            "GetNodePublishUrl.get_url_from_node",
            return_value="dummy-url"
        )
        self.mocked_get_publish_url = self.get_publish_url_patcher.start()
        self.addCleanup(self.get_publish_url_patcher.stop)

    def test_assert_multiple_publication_call(self):
        publish_program_trees_using_node_service._bulk_publish([
            self.minor,
            self.deepening,
            self.major,
            self.training
        ])
        self.assertEqual(self.mocked_requests_get.call_count, 4)


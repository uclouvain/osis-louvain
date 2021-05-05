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
import threading
from unittest.mock import patch

from django.http import HttpResponse
from django.test import override_settings

from program_management.ddd import command
from program_management.ddd.service.write import publish_program_trees_using_node_service
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from testing.testcases import DDDTestCase


def mock_thread_start(self):
    self._target(*self._args, **self._kwargs)


class TestPublishProgramTreesUsingNodeService(DDDTestCase):
    def setUp(self):
        super().setUp()
        self.program_tree = ProgramTreeFactory(persist=True)

        self.cmd = command.PublishProgramTreesVersionUsingNodeCommand(
            code=self.program_tree.root_node.code,
            year=self.program_tree.root_node.year
        )

        self.mock_get = self.mock_service("requests.get", return_value=HttpResponse)

    @patch.object(threading.Thread, "start", mock_thread_start)
    @override_settings(ESB_API_URL="esb", ESB_REFRESH_PEDAGOGY_ENDPOINT="{year}{code}")
    def test_publish_call_seperate_thread(self):
        publish_program_trees_using_node_service.publish_program_trees_using_node(self.cmd)

        self.assertTrue(
            self.mock_get.call_args[0],
            "esb/{}{}".format(self.cmd.year, self.cmd.code)
        )




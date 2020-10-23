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

from django.test import SimpleTestCase

from program_management.ddd.domain.exception import NodeHaveLinkException
from program_management.ddd.validators._node_have_link import NodeHaveLinkValidator
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestNodeHaveLinkValidator(SimpleTestCase):
    def setUp(self):
        self.node = NodeGroupYearFactory()

    @mock.patch('program_management.ddd.service.read.search_program_trees_using_node_service'
                '.search_program_trees_using_node')
    def test_should_raise_exception_if_node_have_links(self, mock_search_tree):
        mock_search_tree.return_value = [ProgramTreeFactory(), ProgramTreeFactory()]

        with self.assertRaises(NodeHaveLinkException):
            NodeHaveLinkValidator(self.node).validate()

    @mock.patch('program_management.ddd.service.read.search_program_trees_using_node_service'
                '.search_program_trees_using_node')
    def test_should_not_raise_exception_when_node_doesnt_have_links(self, mock_search_tree):
        mock_search_tree.return_value = []

        NodeHaveLinkValidator(self.node).validate()

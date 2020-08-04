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
from django.test import TestCase
from mock import patch

from program_management.ddd.domain.program_tree import ProgramTree
from program_management.serializers.program_tree_view import program_tree_view_serializer
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory


class TestProgramTreeViewSerializer(TestCase):
    def setUp(self):
        """
        root_node
        |-----common_core
             |---- LDROI100A (UE)
        |----subgroup1
             |---- LDROI120B (UE)
             |----subgroup2
                  |---- LDROI100A (UE)
        :return:
        """
        self.root_node = NodeGroupYearFactory(node_id=1, code="LBIR100B", title="Bachelier en droit", year=2018)
        self.common_core = NodeGroupYearFactory(node_id=2, code="LGROUP100A", title="Tronc commun", year=2018)
        self.ldroi100a = NodeLearningUnitYearFactory(node_id=3, code="LDROI100A", title="Introduction", year=2018)
        self.ldroi120b = NodeLearningUnitYearFactory(node_id=4, code="LDROI120B", title="Séminaire", year=2018)
        self.subgroup1 = NodeGroupYearFactory(node_id=5, code="LSUBGR100G", title="Sous-groupe 1", year=2018)
        self.subgroup2 = NodeGroupYearFactory(node_id=6, code="LSUBGR150G", title="Sous-groupe 2", year=2018)

        LinkFactory(parent=self.root_node, child=self.common_core)
        LinkFactory(parent=self.common_core, child=self.ldroi100a)
        LinkFactory(parent=self.root_node, child=self.subgroup1)
        LinkFactory(parent=self.subgroup1, child=self.ldroi120b)
        LinkFactory(parent=self.subgroup1, child=self.subgroup2)
        LinkFactory(parent=self.subgroup2, child=self.ldroi100a)

        self.tree = ProgramTree(root_node=self.root_node)

    @patch('program_management.serializers.node_view.serialize_children')
    def test_serialize_program_tree_ensure_context_have_root_keys(self, mock):
        program_tree_view_serializer(self.tree)
        context_kwarg = mock.call_args[1]['context']
        self.assertEqual(context_kwarg['root'], self.tree.root_node)

    def test_serialize_program_tree_assert_keys_of_root_element(self):
        serialized_data = program_tree_view_serializer(self.tree)
        expected_keys = ['text', 'icon', 'children', 'a_attr', 'id']

        self.assertSetEqual(set(serialized_data.keys()), set(expected_keys))

    def test_serialize_program_tree_assert_keys_of_root_element_a_attr(self):
        serialized_data = program_tree_view_serializer(self.tree)
        expected_keys = [
            'element_id', 'element_type', 'element_code', 'element_year', 'href', 'paste_url',
            'search_url'
        ]

        self.assertSetEqual(set(serialized_data["a_attr"].keys()), set(expected_keys))

    def test_serialize_program_tree_assert_node_child_element(self):
        serialized_data = program_tree_view_serializer(self.tree)

        self.assertIsInstance(serialized_data['children'], list)
        self.assertEqual(
            serialized_data['children'][0]['path'],
            "|".join([str(self.root_node.pk), str(self.common_core.pk)]),
        )
        self.assertEqual(
            serialized_data['children'][0]['path'],
            serialized_data['children'][0]['id']
        )
        expected_text = self.common_core.code + " - " + self.common_core.title
        self.assertEqual(serialized_data['children'][0]['text'], expected_text)
        self.assertEqual(serialized_data['children'][0]['icon'], None)
        self.assertIsInstance(serialized_data['children'][0]['children'], list)

    def test_serialize_program_tree_assert_keys_of_node_a_attr(self):
        serialized_data = program_tree_view_serializer(self.tree)
        expected_keys = [
            "path", "href", "root", "group_element_year", "element_id", "element_type", "element_code", "element_year",
            "title", "paste_url", "detach_url", "modify_url", "search_url"
        ]

        a_attr = serialized_data['children'][0]['a_attr']
        self.assertIsInstance(a_attr, dict)
        self.assertSetEqual(set(a_attr.keys()), set(expected_keys))

    def test_serialize_program_tree_text(self):
        serialized_data = program_tree_view_serializer(self.tree)
        self.assertEqual(serialized_data['text'],
                         "{} - {}".format(self.root_node.code, self.root_node.title))

    @patch("program_management.serializers.program_tree_view.__get_tree_version_label", return_value='[CEMS]')
    def test_serialize_program_tree_for_version_text(self, mock):
        serialized_data = program_tree_view_serializer(self.tree)
        self.assertEqual(serialized_data['text'],
                         "{} - {}{}".format(self.root_node.code, self.root_node.title, "[CEMS]"))

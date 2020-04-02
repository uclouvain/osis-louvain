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

from program_management.ddd.domain.program_tree import ProgramTree
from program_management.forms.tree.detach import DetachNodeForm
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory


class TestDetachNodeForm(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        """
        DROI2M
        |---Common Core
            |---Learning unit
        |---SUBGROUP 2
        """
        root_node = NodeGroupYearFactory(acronym='DROI2M')
        common_core = NodeGroupYearFactory(acronym='TCDRO200M')
        learning_unit = NodeLearningUnitYearFactory(acronym='LDROI1200')
        subgroup = NodeGroupYearFactory(acronym='LPOR100G')

        common_core.add_child(learning_unit)
        root_node.add_child(common_core)
        root_node.add_child(subgroup)
        cls.tree = ProgramTree(root_node)
        super().setUpClass()

    def test_invalid_form_case_path_is_not_valid(self):
        form_instance = DetachNodeForm(self.tree, data={'path': 'dummy_path'})
        self.assertFalse(form_instance.is_valid())
        self.assertTrue(form_instance.errors['path'])

    @mock.patch('program_management.ddd.service.detach_node_service.detach_node')
    def test_valid_form_assert_called_detach_node_service(self, mock_detach_node):
        common_core_path = "|".join([
            str(self.tree.root_node.node_id),
            str(self.tree.root_node.children[0].child.node_id)]
        )
        form_instance = DetachNodeForm(self.tree, data={'path': common_core_path})
        self.assertTrue(form_instance.is_valid())
        form_instance.save()
        self.assertTrue(mock_detach_node.called)

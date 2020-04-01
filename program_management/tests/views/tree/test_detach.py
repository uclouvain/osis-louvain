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

from django.test import TestCase
from django.urls import reverse

from base.tests.factories.person import PersonFactory
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.forms.tree.detach import DetachNodeForm
from program_management.tests.ddd.factories.node import NodeEducationGroupYearFactory, NodeLearningUnitYearFactory


class TestDetachNodeView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.person = PersonFactory()

    def setUp(self):
        self.tree = self.setUpTreeData()
        self.url = reverse("tree_detach_node", kwargs={'root_id': self.tree.root_node.pk})
        self.client.force_login(self.person.user)

        fetch_tree_patcher = mock.patch('program_management.ddd.repositories.load_tree.load', return_value=self.tree)
        fetch_tree_patcher.start()
        self.addCleanup(fetch_tree_patcher.stop)

    def setUpTreeData(self):
        """
           |BIR1BA
           |----LBIR150T (common-core)
                |---LBIR1110 (UE)
           |----LBIR101G (subgroup)
        """
        root_node = NodeEducationGroupYearFactory(acronym="BIR1BA")
        common_core = NodeEducationGroupYearFactory(acronym="LBIR150T")
        learning_unit_node = NodeLearningUnitYearFactory(acronym='LBIR1110')
        subgroup = NodeEducationGroupYearFactory(acronym="LBIR101G")

        common_core.add_child(learning_unit_node)
        root_node.add_child(common_core)
        root_node.add_child(subgroup)
        return ProgramTree(root_node)

    def test_allowed_http_method_when_user_is_not_logged(self):
        self.client.logout()

        allowed_method = ['get', 'post']
        for method in allowed_method:
            response = getattr(self.client, method)(self.url)
            self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_get_ensure_path_args_is_set_as_initial_on_form(self):
        path_to_detach = "|".join([
            str(self.tree.root_node.pk),
            str(self.tree.root_node.children[0].child.pk)
        ])

        response = self.client.get(self.url, data={'path': path_to_detach})
        self.assertTemplateUsed(response, 'tree/detach_confirmation.html')

        self.assertTrue('form' in response.context)
        self.assertIsInstance(response.context['form'], DetachNodeForm)
        self.assertDictEqual(response.context['form'].initial, {'path': path_to_detach})

    def test_post_with_invalid_path(self):
        response = self.client.post(self.url, data={'path': 'dummy_path'})
        self.assertTemplateUsed(response, 'tree/detach_confirmation.html')

        self.assertTrue('form' in response.context)
        self.assertIsInstance(response.context['form'], DetachNodeForm)
        self.assertTrue(response.context['form'].errors['path'])

    @mock.patch('program_management.forms.tree.detach.DetachNodeForm.save', return_value=None)
    def test_post_with_valid_path_ensure_form_save_called(self, mock_form_save):
        path_to_detach = "|".join([
            str(self.tree.root_node.pk),
            str(self.tree.root_node.children[0].child.pk)
        ])
        self.client.post(self.url, data={'path': path_to_detach})

        self.assertTrue(mock_form_save.called)

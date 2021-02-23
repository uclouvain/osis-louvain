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

from django.http import HttpResponse, HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.person import PersonFactory
from education_group.tests.factories.group_year import GroupYearFactory
from osis_role.contrib.views import AjaxPermissionRequiredMixin
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION, STANDARD
from program_management.forms.content import LinkForm, ContentFormSet
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionIdentityFactory


def form_valid_effect(form: LinkForm):
    return True


def form_save_effect():
    return [LinkFactory()]


class TestUpdateLinkView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.person = PersonFactory()

    def setUp(self):
        self.tree = self.setUpTreeData()
        self.parent = self.tree.root_node
        self.child = self.tree.root_node.children_as_nodes[0]
        self.url = reverse("tree_update_link", args=[
            self.parent.code, self.parent.year, self.child.code, self.child.year
        ])
        self.client.force_login(self.person.user)
        self.setUpPatchers()

    def setUpPatchers(self):
        get_tree_patcher = mock.patch(
            'program_management.ddd.service.read.get_program_tree_service.get_program_tree',
            return_value=self.tree
        )
        self.get_tree_patcher_mock = get_tree_patcher.start()
        self.addCleanup(get_tree_patcher.stop)

        get_link_patcher = mock.patch(
            'program_management.ddd.domain.program_tree.ProgramTree.get_first_link_occurence_using_node',
            return_value=LinkFactory(parent=self.parent, child=self.child)
        )
        self.get_link_patcher_mock = get_link_patcher.start()
        self.addCleanup(get_link_patcher.stop)

        get_perm_object_patcher = mock.patch(
            'program_management.views.tree.update.UpdateLinkView.get_permission_object',
            return_value=GroupYearFactory(
                partial_acronym=self.tree.root_node.code, academic_year__year=self.tree.root_node.year
            )
        )
        get_perm_object_patcher.start()
        self.addCleanup(get_perm_object_patcher.stop)

        get_node_patcher = mock.patch(
            'program_management.ddd.repositories.node.NodeRepository.get',
            return_value=self.child
        )
        self.get_node_patcher_mock = get_node_patcher.start()
        self.addCleanup(get_node_patcher.stop)

        permission_patcher = mock.patch.object(AjaxPermissionRequiredMixin, "has_permission")
        self.permission_mock = permission_patcher.start()
        self.permission_mock.return_value = True
        self.addCleanup(permission_patcher.stop)

    def setUpTreeData(self):
        """
           |BIR1BA
           |----LBIR150T
        """
        root_node = NodeGroupYearFactory(code="BIR1BA")
        common_core = NodeGroupYearFactory(code="LBIR150T")
        root_node.add_child(common_core)
        return ProgramTreeFactory(root_node=root_node)

    def test_should_return_form_when_update_action_is_chosen(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'tree/link_update_inner.html')
        self.assertIsInstance(response.context['content_formset'], ContentFormSet)

    def test_should_show_access_denied_when_user_has_not_perm(self):
        self.permission_mock.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    @mock.patch.object(ContentFormSet, 'is_valid', new=form_valid_effect)
    @mock.patch.object(ContentFormSet, 'save')
    @mock.patch(
        'program_management.ddd.domain.service.identity_search.ProgramTreeVersionIdentitySearch.get_from_node_identity'
    )
    @mock.patch('program_management.ddd.repositories.program_tree.ProgramTreeRepository.get')
    def test_should_call_update_link_service_when_post_data_is_valid(
            self,
            mock_get_tree,
            mock_get_tree_version,
            mock_form_save
    ):
        mock_get_tree.return_value = self.tree
        mock_get_tree_version.return_value = ProgramTreeVersionIdentityFactory(
            transition_name=NOT_A_TRANSITION,
            version_name=STANDARD
        )
        mock_form_save.side_effect = form_save_effect
        self.client.post(self.url, data={})
        self.assertTrue(mock_form_save.called, msg="View must call form save method")

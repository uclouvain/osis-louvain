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
from typing import List
from unittest import mock

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.tests.factories.person import PersonFactory
from education_group.ddd.domain.exception import GroupNotFoundException
from education_group.ddd.domain.group import GroupIdentity
from education_group.ddd.factories.group import GroupFactory
from education_group.forms.content import ContentFormSet
from education_group.forms.group import GroupUpdateForm
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.views.proxy.read import Tab
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestUpdateGroupGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = GroupFactory()
        cls.program_tree = ProgramTreeFactory()

        cls.group.entity_identity = GroupIdentity(year=2018, code='LBIR100M')
        cls.central_manager = CentralManagerFactory()
        cls.url = reverse('group_update', kwargs={'year': cls.group.year, 'code': cls.group.code})

    def setUp(self) -> None:
        self.get_group_patcher = mock.patch(
            "education_group.views.group.update.get_group_service.get_group",
            return_value=self.group
        )
        self.mocked_get_group = self.get_group_patcher.start()
        self.addCleanup(self.get_group_patcher.stop)

        self.get_program_tree_patcher = mock.patch(
            "education_group.views.group.update.get_program_tree_service.get_program_tree",
            return_value=self.program_tree
        )
        self.mocked_get_program_tree = self.get_program_tree_patcher.start()
        self.addCleanup(self.get_program_tree_patcher.stop)

        self.client.force_login(self.central_manager.person.user)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch('education_group.views.group.update.get_group_service.get_group', side_effect=GroupNotFoundException)
    def test_assert_404_when_group_not_found(self, mock_get_group):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "education_group_app/group/upsert/update.html")

    def test_assert_context(self):
        response = self.client.get(self.url)

        self.assertIsInstance(response.context['group_form'], GroupUpdateForm)
        self.assertIsInstance(response.context['content_formset'], ContentFormSet)
        self.assertIsInstance(response.context['tabs'], List)
        self.assertIsInstance(response.context['cancel_url'], str)

    @mock.patch('education_group.views.group.update.GroupUpdateView.get_children_objs')
    @mock.patch('education_group.views.group.update.GroupUpdateView.get_program_tree_obj')
    def test_assert_contains_identification_and_content_tabs_when_group_have_children(self,
                                                                                      mock_get_program_tree,
                                                                                      mock_get_children_obj):
        root_link = LinkFactory()
        program_tree = ProgramTreeFactory(root_node=root_link.parent)
        mock_get_program_tree.return_value = program_tree
        mock_get_children_obj.return_value = [GroupFactory()]

        response = self.client.get(self.url)

        self.assertListEqual(
            response.context['tabs'],
            [{
                "id": "identification",
                "text": _("Identification"),
                "active": True,
                "display": True,
                "include_html": "education_group_app/group/upsert/identification_form.html"
            }, {
                "id": "content",
                "text": _("Content"),
                "active": False,
                "display": True,
                "include_html": "education_group_app/group/upsert/content_form.html"
            }]
        )

    @mock.patch('education_group.views.group.update.GroupUpdateView.get_children_objs')
    @mock.patch('education_group.views.group.update.GroupUpdateView.get_program_tree_obj')
    def test_assert_content_tab_active_when_tab_queryparm(self, mock_get_program_tree, mock_get_children_obj):
        root_link = LinkFactory()
        program_tree = ProgramTreeFactory(root_node=root_link.parent)
        mock_get_program_tree.return_value = program_tree
        mock_get_children_obj.return_value = [GroupFactory()]

        url_with_tab_queryparam = self.url + "?tab={}".format(Tab.CONTENT)
        response = self.client.get(url_with_tab_queryparam)

        self.assertFalse(response.context['tabs'][0]['active'])
        self.assertTrue(response.context['tabs'][1]['active'])

    @mock.patch('education_group.views.group.update.GroupUpdateView.get_program_tree_obj')
    def test_assert_contains_only_identification_tabs_when_group_dont_have_children(self, mock_get_program_tree):
        mock_get_program_tree.return_value = ProgramTreeFactory()
        response = self.client.get(self.url)

        self.assertListEqual(
            response.context['tabs'],
            [{
                "id": "identification",
                "text": _("Identification"),
                "active": True,
                "display": True,
                "include_html": "education_group_app/group/upsert/identification_form.html"
            }, {
                "id": "content",
                "text": _("Content"),
                "active": False,
                "display": False,
                "include_html": "education_group_app/group/upsert/content_form.html"
            }]
        )

    def test_assert_cancel_url_computed(self):
        response = self.client.get(self.url)

        expected_url = reverse('element_identification', kwargs={'year': self.group.year, 'code': self.group.code})
        self.assertEqual(response.context['cancel_url'], expected_url)

    def test_assert_cancel_url_keep_path_queryparam(self):
        url_with_path = self.url + "?path=25656565|56565"

        response = self.client.get(url_with_path)
        expected_url = reverse('element_identification', kwargs={'year': self.group.year, 'code': self.group.code}) + \
            "?path=25656565|56565"
        self.assertEqual(response.context['cancel_url'], expected_url)

    def test_assert_group_form_initial_computed(self):
        response = self.client.get(self.url)

        initials = response.context['group_form'].initial
        self.assertEqual(initials['code'], self.group.code)
        self.assertEqual(initials['abbreviated_title'], self.group.abbreviated_title)
        self.assertEqual(initials['title_fr'], self.group.titles.title_fr)
        self.assertEqual(initials['title_en'], self.group.titles.title_en)
        self.assertEqual(initials['credits'], self.group.credits)
        self.assertEqual(initials['constraint_type'], self.group.content_constraint.type.name)
        self.assertEqual(initials['min_constraint'], self.group.content_constraint.minimum)
        self.assertEqual(initials['max_constraint'], self.group.content_constraint.maximum)
        self.assertEqual(initials['remark_fr'], self.group.remark.text_fr)
        self.assertEqual(initials['remark_en'], self.group.remark.text_en)

    @mock.patch('education_group.views.group.update.GroupUpdateView.get_children_objs')
    @mock.patch('education_group.views.group.update.GroupUpdateView.get_program_tree_obj')
    def test_assert_content_formset_initial_computed(self, mock_get_program_tree_objs, mock_get_children_objs):
        link_child_1 = LinkFactory()
        mock_get_program_tree_objs.return_value = ProgramTreeFactory(root_node=link_child_1.parent)
        mock_get_children_objs.return_value = [
            GroupFactory(
                entity_identity=GroupIdentity(code=link_child_1.child.code, year=link_child_1.child.year)
            )
        ]

        response = self.client.get(self.url)

        initials = response.context['content_formset'].initial
        self.assertEqual(len(initials), 1)

        self.assertEqual(initials[0]['relative_credits'], link_child_1.relative_credits)
        self.assertEqual(initials[0]['link_type'], link_child_1.link_type)
        self.assertEqual(initials[0]['access_condition'], link_child_1.access_condition)
        self.assertEqual(initials[0]['block'], link_child_1.block)
        self.assertEqual(initials[0]['comment_fr'], link_child_1.comment)
        self.assertEqual(initials[0]['comment_en'], link_child_1.comment_english)


class TestUpdateGroupPostMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group = GroupFactory()
        cls.program_tree = ProgramTreeFactory()

        cls.group.entity_identity = GroupIdentity(year=2018, code='LBIR100M')
        cls.central_manager = CentralManagerFactory()
        cls.url = reverse('group_update', kwargs={'year': cls.group.year, 'code': cls.group.code})

    def setUp(self) -> None:
        self.get_group_patcher = mock.patch(
            "education_group.views.group.update.get_group_service.get_group",
            return_value=self.group
        )
        self.mocked_get_group = self.get_group_patcher.start()
        self.addCleanup(self.get_group_patcher.stop)

        self.get_program_tree_patcher = mock.patch(
            "education_group.views.group.update.get_program_tree_service.get_program_tree",
            return_value=self.program_tree
        )
        self.mocked_get_program_tree = self.get_program_tree_patcher.start()
        self.addCleanup(self.get_program_tree_patcher.stop)

        self.update_group_patcher = mock.patch(
            "education_group.views.group.update.update_group_service.update_group",
            return_value=self.group
        )
        self.mocked_update_group = self.update_group_patcher.start()
        self.addCleanup(self.update_group_patcher.stop)

        self.update_links_patcher = mock.patch(
            "education_group.views.group.update.update_link_service.bulk_update_links",
            return_value=[]
        )
        self.mocked_update_links = self.update_links_patcher.start()
        self.addCleanup(self.update_links_patcher.stop)

        self.client.force_login(self.central_manager.person.user)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch('education_group.views.group.update.get_group_service.get_group', side_effect=GroupNotFoundException)
    def test_assert_404_when_group_not_found(self, mock_get_group):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    @mock.patch('education_group.views.group.update.GroupUpdateView.is_all_forms_valid')
    @mock.patch('education_group.views.group.update.ContentFormSet')
    @mock.patch('education_group.views.group.update.GroupUpdateForm')
    def test_case_all_forms_valid_assert_redirection(self, mock_group_form, mock_content_formset,
                                                     mock_is_all_form_valid):
        mock_group_form.return_value.is_valid.return_value = True
        mock_content_formset.return_value.is_valid.return_value = True
        mock_is_all_form_valid.return_value = True

        expected_redirect = reverse(
            'element_identification', kwargs={'code': self.group.code, 'year': self.group.year}
        )
        response = self.client.post(self.url, data={})
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)

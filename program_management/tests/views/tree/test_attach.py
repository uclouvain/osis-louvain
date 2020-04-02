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
import mock
from django.contrib import messages
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.ddd.utils.validation_message import MessageLevel, BusinessValidationMessage
from base.models.enums.education_group_types import GroupType
from base.tests.factories.education_group_year import GroupFactory
from base.tests.factories.person import PersonFactory
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.forms.tree.attach import AttachNodeFormSet, AttachNodeForm
from program_management.tests.ddd.factories.node import NodeEducationGroupYearFactory, NodeLearningUnitYearFactory


def form_valid_effect(formset: AttachNodeFormSet):
    for form in formset:
        form.cleaned_data = {}
    return True


class TestAttachNodeView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.person = PersonFactory()

    def setUp(self):
        self.tree = self.setUpTreeData()
        self.url = reverse("tree_attach_node", kwargs={'root_id': self.tree.root_node.pk})
        self.client.force_login(self.person.user)

        fetch_tree_patcher = mock.patch('program_management.ddd.repositories.load_tree.load', return_value=self.tree)
        fetch_tree_patcher.start()
        self.addCleanup(fetch_tree_patcher.stop)

        self.fetch_from_cache_patcher = mock.patch(
            'program_management.business.group_element_years.management.fetch_elements_selected',
            return_value=[]
        )
        self.fetch_from_cache_patcher.start()
        self.addCleanup(self.fetch_from_cache_patcher.stop)

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

    def test_get_method_when_no_data_selected_on_cache(self):
        to_path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[0].child.pk)])
        response = self.client.get(self.url + "?to_path=" + to_path)
        self.assertEquals(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'tree/attach_inner.html')

        msgs = [m.message for m in messages.get_messages(response.wsgi_request)]
        self.assertEqual(msgs, [_("Please cut or copy an item before attach it")])

    @mock.patch('program_management.business.group_element_years.management.fetch_elements_selected')
    def test_get_method_when_education_group_year_element_is_selected(self, mock_cache_elems):
        subgroup_to_attach = GroupFactory(
            academic_year__year=self.tree.root_node.year,
            education_group_type__name=GroupType.SUB_GROUP.name,
        )
        mock_cache_elems.return_value = [subgroup_to_attach]

        # To path :  BIR1BA ---> COMMON_CORE
        to_path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[0].child.pk)])
        response = self.client.get(self.url + "?to_path=" + to_path)
        self.assertEquals(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'tree/attach_inner.html')

        self.assertIn('formset', response.context, msg="Probably there are no item selected on cache")
        self.assertIsInstance(response.context['formset'], AttachNodeFormSet)
        self.assertEquals(len(response.context['formset'].forms), 1)
        self.assertIsInstance(response.context['formset'].forms[0], AttachNodeForm)

    @mock.patch('program_management.business.group_element_years.management.fetch_elements_selected')
    def test_get_method_when_multiple_education_group_year_element_are_selected(self, mock_cache_elems):
        subgroup_to_attach = GroupFactory(
            academic_year__year=self.tree.root_node.year,
            education_group_type__name=GroupType.SUB_GROUP.name,
        )
        subgroup_to_attach_2 = GroupFactory(
            academic_year__year=self.tree.root_node.year,
            education_group_type__name=GroupType.SUB_GROUP.name,
        )
        mock_cache_elems.return_value = [subgroup_to_attach, subgroup_to_attach_2]

        # To path :  BIR1BA ---> LBIR101G
        to_path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[1].child.pk)])
        response = self.client.get(self.url + "?to_path=" + to_path)
        self.assertEquals(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'tree/attach_inner.html')

        self.assertIn('formset', response.context, msg="Probably there are no item selected on cache")
        self.assertIsInstance(response.context['formset'], AttachNodeFormSet)
        self.assertEquals(len(response.context['formset'].forms), 2)

    @mock.patch('program_management.business.group_element_years.management.fetch_elements_selected')
    @mock.patch('program_management.forms.tree.attach.AttachNodeFormSet.is_valid')
    def test_post_method_case_formset_invalid(self, mock_formset_is_valid, mock_cache_elems):
        subgroup_to_attach = GroupFactory(
            academic_year__year=self.tree.root_node.year,
            education_group_type__name=GroupType.SUB_GROUP.name,
        )
        mock_cache_elems.return_value = [subgroup_to_attach]
        mock_formset_is_valid.return_value = False

        # To path :  BIR1BA ---> LBIR101G
        to_path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[1].child.pk)])
        response = self.client.post(self.url + "?to_path=" + to_path)

        self.assertTemplateUsed(response, 'tree/attach_inner.html')
        self.assertIn('formset', response.context, msg="Probably there are no item selected on cache")
        self.assertIsInstance(response.context['formset'], AttachNodeFormSet)

    @mock.patch('program_management.ddd.service.attach_node_service.attach_node')
    @mock.patch.object(AttachNodeFormSet, 'is_valid', new=form_valid_effect)
    @mock.patch('program_management.business.group_element_years.management.fetch_elements_selected')
    def test_post_method_case_formset_valid(self, mock_cache_elems, mock_service):
        mock_service.return_value = [BusinessValidationMessage('Success', MessageLevel.SUCCESS)]
        subgroup_to_attach = GroupFactory(
            academic_year__year=self.tree.root_node.year,
            education_group_type__name=GroupType.SUB_GROUP.name,
        )
        mock_cache_elems.return_value = [subgroup_to_attach]

        # To path :  BIR1BA ---> LBIR101G
        to_path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[1].child.pk)])
        response = self.client.post(self.url + "?to_path=" + to_path)

        msgs = [m.message for m in messages.get_messages(response.wsgi_request)]
        self.assertEqual(msgs, ['Success'])

        self.assertTrue(
            mock_service.called,
            msg="View must call attach node service (and not another layer) "
                "because the 'attach node' action uses multiple domain objects"
        )

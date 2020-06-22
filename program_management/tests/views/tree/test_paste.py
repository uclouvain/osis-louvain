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

from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from waffle.testutils import override_flag

import osis_common.ddd.interface
from base.ddd.utils import business_validator
from base.models.enums.education_group_types import GroupType
from base.models.enums.link_type import LinkTypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory
from base.utils.cache import ElementCache
from base.utils.urls import reverse_with_get
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command
from program_management.ddd.domain import link
from program_management.forms.tree.paste import PasteNodesFormset, PasteNodeForm
from program_management.tests.ddd.factories.node import NodeEducationGroupYearFactory, NodeLearningUnitYearFactory, \
    NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.factories.element import ElementGroupYearFactory


def form_valid_effect(formset: PasteNodesFormset):
    for form in formset:
        form.cleaned_data = {}
    return True


class TestPasteNodeView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.person = PersonFactory()

    def setUp(self):
        self.tree = self.setUpTreeData()
        self.url = reverse("tree_paste_node")
        self.client.force_login(self.person.user)

        fetch_tree_patcher = mock.patch('program_management.ddd.repositories.load_tree.load', return_value=self.tree)
        fetch_tree_patcher.start()
        self.addCleanup(fetch_tree_patcher.stop)

        self.fetch_from_cache_patcher = mock.patch(
            'program_management.ddd.service.read.element_selected_service.retrieve_element_selected',
            return_value=[]
        )
        self.fetch_from_cache_patcher.start()
        self.addCleanup(self.fetch_from_cache_patcher.stop)

        self.get_form_class_patcher = mock.patch(
            'program_management.forms.tree.paste._get_form_class',
            return_value=PasteNodeForm
        )
        self.get_form_class_patcher.start()
        self.addCleanup(self.get_form_class_patcher.stop)

        permission_patcher = mock.patch.object(PermissionRequiredMixin, "has_permission")
        self.permission_mock = permission_patcher.start()
        self.permission_mock.return_value = True
        self.addCleanup(permission_patcher.stop)

    def setUpTreeData(self):
        """
           |BIR1BA
           |----LBIR150T (common-core)
                |---LBIR1110 (UE)
           |----LBIR101G (subgroup)
        """
        root_node = NodeEducationGroupYearFactory(code="BIR1BA")
        common_core = NodeEducationGroupYearFactory(code="LBIR150T")
        learning_unit_node = NodeLearningUnitYearFactory(code='LBIR1110')
        subgroup = NodeEducationGroupYearFactory(code="LBIR101G")

        common_core.add_child(learning_unit_node)
        root_node.add_child(common_core)
        root_node.add_child(subgroup)
        return ProgramTreeFactory(root_node=root_node)

    def test_should_return_error_message_when_no_nodes_selected_to_paste(self):
        path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[0].child.pk)])
        response = self.client.get(self.url, data={"path": path})
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'tree/paste_inner.html')

        msgs = [m.message for m in messages.get_messages(response.wsgi_request)]
        self.assertEqual(msgs, [_("Please cut or copy an item before paste")])
        self.assertTrue(self.permission_mock.called)

    @mock.patch('program_management.ddd.service.read.element_selected_service.retrieve_element_selected')
    def test_should_return_formset_when_elements_are_selected(self, mock_cache_elems):
        subgroup_to_attach = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP)
        subgroup_to_attach_2 = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP,)

        # To path :  BIR1BA ---> LBIR101G
        path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[1].child.pk)])
        response = self.client.get(
            self.url,
            data={
                "path": path,
                "codes": [subgroup_to_attach.code, subgroup_to_attach_2.code],
                "year": subgroup_to_attach.year
            }
        )
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'tree/paste_inner.html')

        self.assertIsInstance(response.context['formset'], PasteNodesFormset)
        self.assertEqual(len(response.context['formset'].forms), 2)

    @mock.patch('program_management.ddd.service.read.element_selected_service.retrieve_element_selected')
    @mock.patch('program_management.forms.tree.paste.PasteNodesFormset.is_valid')
    def test_should_rereturn_fromset_when_post_data_are_not_valid(self, mock_formset_is_valid, mock_cache_elems):
        subgroup_to_attach = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP)
        mock_cache_elems.return_value = {
            "element_code": subgroup_to_attach.code,
            "element_year": subgroup_to_attach.year,
            "path_to_detach": None
        }
        mock_formset_is_valid.return_value = False

        # To path :  BIR1BA ---> LBIR101G
        path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[1].child.pk)])
        response = self.client.post(self.url + "?path=" + path)

        self.assertTemplateUsed(response, 'tree/paste_inner.html')
        self.assertIsInstance(response.context['formset'], PasteNodesFormset)

    @mock.patch('program_management.ddd.service.write.paste_element_service.paste_element')
    @mock.patch.object(PasteNodesFormset, 'is_valid', new=form_valid_effect)
    @mock.patch.object(PasteNodeForm, 'is_valid')
    @mock.patch('program_management.ddd.service.read.element_selected_service.retrieve_element_selected')
    def test_should_call_paste_node_service_when_post_data_are_valid(
            self,
            mock_cache_elems,
            mock_form_valid,
            mock_service
    ):
        subgroup_to_attach = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP,)
        mock_cache_elems.return_value = {
            "element_code": subgroup_to_attach.code,
            "element_year": subgroup_to_attach.year,
            "path_to_detach": None
        }
        mock_form_valid.return_value = True
        mock_service.return_value = link.LinkIdentity(
            parent_code=self.tree.root_node.children[1].child.code,
            child_code=subgroup_to_attach.code,
            parent_year=self.tree.root_node.children[1].child.year,
            child_year=subgroup_to_attach.year
        )

        # To path :  BIR1BA ---> LBIR101G
        path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[1].child.pk)])
        self.client.post(self.url + "?path=" + path)

        self.assertTrue(
            mock_service.called,
            msg="View must call attach node service (and not another layer) "
                "because the 'attach node' action uses multiple domain objects"
        )


@override_flag('education_group_update', active=True)
class TestPasteWithCutView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.root_element = ElementGroupYearFactory(group_year__academic_year=cls.academic_year)
        cls.group_element_year = GroupElementYearFactory(
            parent__academic_year=cls.academic_year,
            generate_element=True
        )
        cls.selected_element = ElementGroupYearFactory(
            group_year__academic_year=cls.academic_year
        )
        GroupElementYearFactory(
            parent_element=cls.root_element,
            child_element=cls.selected_element
        )

        path_to_attach = "|".join([str(cls.root_element.id), str(cls.selected_element.id)])
        cls.url = reverse_with_get("tree_paste_node", get={"path": path_to_attach})
        cls.person = PersonFactory()

    def setUp(self):
        self.client.force_login(self.person.user)

        permission_patcher = mock.patch.object(User, "has_perms")
        self.permission_mock = permission_patcher.start()
        self.permission_mock.return_value = True
        self.addCleanup(permission_patcher.stop)
        self.addCleanup(ElementCache(self.person.user).clear)

    def test_should_check_attach_and_detach_permission(self):
        AuthorizedRelationshipFactory(
            parent_type=self.selected_element.group_year.education_group_type,
            child_type=self.group_element_year.child_element.group_year.education_group_type,
            min_count_authorized=0,
            max_count_authorized=None
        )
        ElementCache(self.person.user.id).save_element_selected(
            element_year=self.academic_year.year,
            element_code=self.group_element_year.child_element.group_year.partial_acronym,
            path_to_detach="|".join([
                str(self.group_element_year.parent_element.id),
                str(self.group_element_year.child_element.id)
            ]),
            action=ElementCache.ElementCacheAction.CUT
        )
        self.client.get(self.url)
        self.permission_mock.assert_has_calls(
            [
                mock.call(("base.can_detach_node",), self.group_element_year.parent_element.group_year),
                mock.call(("base.can_attach_node",), self.selected_element.group_year)
            ]

        )
        self.assertTrue(self.permission_mock.called)

    @mock.patch("program_management.ddd.service.write.paste_element_service.paste_element")
    def test_move(self, mock_paste_service):
        AuthorizedRelationshipFactory(
            parent_type=self.selected_element.group_year.education_group_type,
            child_type=self.group_element_year.child_element.group_year.education_group_type,
            min_count_authorized=0,
            max_count_authorized=None
        )
        mock_paste_service.return_value = link.LinkIdentity(
            parent_code=self.group_element_year.parent_element.group_year.partial_acronym,
            child_code=self.group_element_year.child_element.group_year.partial_acronym,
            parent_year=self.academic_year.year,
            child_year=self.academic_year.year
        )
        detach_path = "|".join(
            [str(self.group_element_year.parent_element.id), str(self.group_element_year.child_element.id)]
        )
        ElementCache(self.person.user.id).save_element_selected(
            element_year=self.group_element_year.child_element.group_year.academic_year.year,
            element_code=self.group_element_year.child_element.group_year.partial_acronym,
            path_to_detach=detach_path,
            action=ElementCache.ElementCacheAction.CUT
        )

        self.client.post(self.url, data={
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1',
            "link_type": LinkTypes.REFERENCE.name
        })

        self.assertEqual(
            mock_paste_service.call_args[0][0].path_where_to_detach,
            detach_path
        )


@override_flag('education_group_update', active=True)
class TestCheckPasteView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

        cls.url = reverse("check_tree_paste_node")
        cls.path = "12|25|98"

    def setUp(self):
        self.client.force_login(self.person.user)

        patcher_check_paste = mock.patch("program_management.ddd.service.read.check_paste_node_service.check_paste")
        self.mock_check_paste = patcher_check_paste.start()
        self.mock_check_paste.return_value = None
        self.addCleanup(patcher_check_paste.stop)

    def test_should_call_check_paste_service_based_on_get_parameters_when_get_parameters_are_filled(self):
        self.client.get(
            self.url,
            data={
                "path": self.path,
                "codes": ["LSINF1254", "LECGE2589"],
                "year": 2021,
            },
            HTTP_ACCEPT="application/json"
        )
        self.mock_check_paste.assert_has_calls(
            [
                mock.call(command.CheckPasteNodeCommand(
                    12,
                    node_to_past_code="LSINF1254",
                    node_to_paste_year=2021,
                    path_to_paste=self.path,
                    path_to_detach=None
                )),
                mock.call(command.CheckPasteNodeCommand(
                    12,
                    node_to_past_code="LECGE2589",
                    node_to_paste_year=2021,
                    path_to_paste=self.path,
                    path_to_detach=None
                ))
            ]
        )

    def test_should_return_error_messages_when_check_paste_service_raises_exception(
            self
    ):
        self.mock_check_paste.side_effect = osis_common.ddd.interface.BusinessExceptions(["Not valid"])
        response = self.client.get(
            self.url,
            data={
                "path": self.path,
                "codes": ["LSINF1254", "LECGE2589"],
                "year": 2021,
            },
            HTTP_ACCEPT="application/json"
        )

        self.assertEqual(
            response.json(),
            {"error_messages": ["Not valid", "Not valid"]}
        )

    def test_should_not_return_error_messages_when_check_paste_service_do_not_raises_excpetion(self):
        response = self.client.get(
            self.url,
            data={
                "path": self.path,
                "codes": ["LSINF1254", "LECGE2589"],
                "year": 2021,
            },
            HTTP_ACCEPT="application/json"
        )

        self.assertEqual(
            response.json(),
            {"error_messages": []}
        )

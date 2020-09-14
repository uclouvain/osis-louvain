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

from django.contrib.messages import get_messages, constants as MSG
from django.http import HttpResponseNotFound, HttpResponse
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

from base.models.enums import education_group_categories
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory
from base.utils.cache import ElementCache
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from program_management.ddd.domain import link
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.validators._authorized_relationship import DetachAuthorizedRelationshipValidator
from program_management.forms.tree.detach import DetachNodeForm
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory, NodeGroupYearFactory
from program_management.tests.ddd.factories.repository.fake import get_fake_program_tree_version_repository
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory
from testing.mocks import MockPatcherMixin


@override_flag('education_group_update', active=True)
class TestDetachNodeView(TestCase, MockPatcherMixin):
    @classmethod
    def setUpTestData(cls):
        """
        root_node
        |-----common_core
             |---- LDROI100A (UE)
        |----subgroup1
             |---- LDROI120B (UE)
             |----subgroup2
                  |---- LDROI1300 (UE)
                  |---- LAGRO2400 (UE)
        :return:
        """
        cls.academic_year = AcademicYearFactory(current=True)
        cls.person = PersonFactory()
        cls.root_node = NodeGroupYearFactory(node_id=1,
                                             code="LBIR100B",
                                             title="Bachelier en droit",
                                             year=cls.academic_year.year)
        cls.common_core = NodeGroupYearFactory(node_id=2,
                                               code="LGROUP100A",
                                               title="Tronc commun",
                                               year=cls.academic_year.year)
        cls.ldroi100a = NodeLearningUnitYearFactory(node_id=3,
                                                    code="LDROI100A",
                                                    common_title_fr="Introduction",
                                                    specific_title_fr="Partie 1",
                                                    year=cls.academic_year.year)
        cls.ldroi120b = NodeLearningUnitYearFactory(node_id=4,
                                                    code="LDROI120B",
                                                    common_title_fr="Séminaire",
                                                    specific_title_fr="Partie 1",
                                                    year=cls.academic_year.year)
        cls.subgroup1 = NodeGroupYearFactory(node_id=5,
                                             code="LSUBGR100G",
                                             title="Sous-groupe 1",
                                             year=cls.academic_year.year)
        cls.subgroup2 = NodeGroupYearFactory(node_id=10,
                                             code="LSUBGR190G",
                                             title="Sous-groupe 2",
                                             year=cls.academic_year.year)

        cls.ldroi1300 = NodeLearningUnitYearFactory(node_id=7,
                                                    code="LDROI1300",
                                                    common_title_fr="Introduction droit",
                                                    specific_title_fr="Partie 1",
                                                    year=cls.academic_year.year)
        cls.lagro2400 = NodeLearningUnitYearFactory(node_id=8,
                                                    code="LAGRO2400",
                                                    common_title_fr="Séminaire agro",
                                                    specific_title_fr="Partie 1",
                                                    year=cls.academic_year.year)

        LinkFactory(parent=cls.root_node, child=cls.common_core)
        LinkFactory(parent=cls.common_core, child=cls.ldroi100a)
        LinkFactory(parent=cls.root_node, child=cls.subgroup1)
        LinkFactory(parent=cls.subgroup1, child=cls.ldroi120b)
        LinkFactory(parent=cls.subgroup1, child=cls.subgroup2)
        LinkFactory(parent=cls.subgroup2, child=cls.ldroi1300)
        LinkFactory(parent=cls.subgroup2, child=cls.lagro2400)

        cls.tree = ProgramTree(root_node=cls.root_node)

        cls.root_egy = EducationGroupYearFactory(id=cls.root_node.node_id,
                                                 education_group_type__category=education_group_categories.TRAINING,
                                                 acronym=cls.root_node.code,
                                                 title=cls.root_node.title,
                                                 academic_year__year=cls.root_node.year)
        cls.egv_root = EducationGroupVersionFactory(
            offer=cls.root_egy,
            version_name='',
        )

        element = ElementGroupYearFactory(group_year__academic_year=cls.academic_year)
        cls.group_element_year = GroupElementYearFactory(
            parent_element=element,
            child_element__group_year__academic_year=cls.academic_year
        )
        cls.person = CentralManagerFactory(entity=element.group_year.management_entity).person
        cls.path_to_detach = '|'.join([
            str(cls.group_element_year.parent_element_id),
            str(cls.group_element_year.child_element_id)
        ])
        cls.url = reverse("tree_detach_node", args=[
            element.id,
        ]) + "?path={}".format(cls.path_to_detach)

    def setUp(self):
        self.client.force_login(self.person.user)
        self._mock_authorized_relationship_validator()
        self.fake_program_tree_version_repo = get_fake_program_tree_version_repository([])

        self.mock_repo(
            "program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository",
            self.fake_program_tree_version_repo
        )

    def _mock_authorized_relationship_validator(self):
        self.validator_patcher = mock.patch.object(
            DetachAuthorizedRelationshipValidator,
            "validate"
        )
        self.mocked_validator = self.validator_patcher.start()
        self.addCleanup(self.validator_patcher.stop)

    @mock.patch("program_management.ddd.service.write.detach_node_service.detach_node")
    def test_should_initialize_path_from_get_parameters_path_value_when_initializing_form(self, mock):
        response = self.client.get(self.url, data={'path': self.path_to_detach})
        self.assertTemplateUsed(response, 'tree/detach_confirmation_inner.html')

        self.assertIsInstance(response.context['form'], DetachNodeForm)
        self.assertDictEqual(response.context['form'].initial, {'path': self.path_to_detach})

    @override_flag('education_group_update', active=False)
    def test_should_return_page_not_found_when_flag_disabled(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_should_return_access_denied_when_user_has_not_sufficient_permissions(self):
        person = PersonFactory()
        self.client.force_login(person.user)
        response = self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/blocks/modal/modal_access_denied.html")

    def test_should_return_detach_confirmation_template_when_ajax_request_is_successful(self):
        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "tree/detach_confirmation_inner.html")

    @mock.patch("program_management.ddd.service.write.detach_node_service.detach_node")
    def test_detach_case_post_success(self, mock_service):
        mock_service.return_value = link.LinkIdentity(
            parent_code=self.group_element_year.parent_element.group_year.partial_acronym,
            child_code=self.group_element_year.child_element.group_year.partial_acronym,
            parent_year=self.group_element_year.parent_element.group_year.academic_year.year,
            child_year=self.group_element_year.child_element.group_year.academic_year.year
        )

        response = self.client.post(
            self.url,
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            data={'path': self.path_to_detach}
        )

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'success': True})
        self.assertEqual(list(get_messages(response.wsgi_request))[0].level, MSG.SUCCESS)
        self.assertTrue(mock_service.called)

    @mock.patch("program_management.ddd.service.write.detach_node_service.detach_node")
    def test_detach_when_element_is_in_clipboard(self, mock_service):
        mock_service.return_value = link.LinkIdentity(
            parent_code=self.group_element_year.parent_element.group_year.partial_acronym,
            child_code=self.group_element_year.child_element.group_year.partial_acronym,
            parent_year=self.group_element_year.parent_element.group_year.academic_year.year,
            child_year=self.group_element_year.child_element.group_year.academic_year.year
        )
        ElementCache(self.person.user).save_element_selected(
            element_code=self.group_element_year.child_element.group_year.partial_acronym,
            element_year=self.group_element_year.child_element.group_year.academic_year.year
        )
        self.client.post(
            self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest', data={'path': self.path_to_detach}
        )
        error_msg = "The clipboard should be cleared if detached element is in clipboard"
        self.assertFalse(ElementCache(self.person.user).cached_data, error_msg)

    @mock.patch("base.models.group_element_year.GroupElementYear.delete")
    def test_detach_when_clipboard_filled_with_different_detached_element(self, mock_delete):
        element_cached = EducationGroupYearFactory()
        ElementCache(self.person.user).save_element_selected(
            element_code=element_cached.partial_acronym,
            element_year=element_cached.academic_year.year
        )
        self.client.post(
            self.url,
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            data={'path': self.path_to_detach}
        )
        error_msg = "The clipboard should not be cleared if element in clipboard is not the detached element"
        self.assertTrue(ElementCache(self.person.user).cached_data, error_msg)

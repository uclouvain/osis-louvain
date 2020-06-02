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

from base.ddd.utils.validation_message import BusinessValidationMessageList, BusinessValidationMessage, MessageLevel
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory
from base.utils.cache import ElementCache
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.auth.faculty_manager import FacultyManagerFactory
from program_management.ddd.validators._authorized_relationship import DetachAuthorizedRelationshipValidator
from program_management.forms.tree.detach import DetachNodeForm


@override_flag('education_group_update', active=True)
class TestDetachNodeView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.education_group_year = EducationGroupYearFactory(academic_year=cls.academic_year)
        cls.group_element_year = GroupElementYearFactory(parent=cls.education_group_year,
                                                         child_branch__academic_year=cls.academic_year)
        cls.person = CentralManagerFactory(entity=cls.education_group_year.management_entity).person
        cls.path_to_detach = '|'.join([str(cls.group_element_year.parent_id), str(cls.group_element_year.child_branch_id)])
        cls.url = reverse("tree_detach_node", args=[
            cls.education_group_year.id,
        ]) + "?path={}".format(cls.path_to_detach)

    def setUp(self):
        self.client.force_login(self.person.user)
        self._mock_authorized_relationship_validator()

    def _mock_authorized_relationship_validator(self):
        self.validator_patcher = mock.patch.object(
            DetachAuthorizedRelationshipValidator,
            "validate"
        )
        self.mocked_validator = self.validator_patcher.start()
        self.addCleanup(self.validator_patcher.stop)

    def test_allowed_http_method_when_user_is_not_logged(self):
        self.client.logout()

        allowed_method = ['get', 'post']
        for method in allowed_method:
            response = getattr(self.client, method)(self.url)
            self.assertIn("/login/?next=", response.url)

    @mock.patch("program_management.ddd.service.detach_node_service.detach_node")
    def test_get_ensure_path_args_is_set_as_initial_on_form(self, mock):

        response = self.client.get(self.url, data={'path': self.path_to_detach})
        self.assertTemplateUsed(response, 'tree/detach_confirmation_inner.html')

        self.assertTrue('form' in response.context)
        self.assertIsInstance(response.context['form'], DetachNodeForm)
        self.assertDictEqual(response.context['form'].initial, {'path': self.path_to_detach})

    def test_post_with_invalid_path(self):
        response = self.client.post(self.url, data={'path': 'dummy_path'})

        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertListEqual(messages, ['Invalid tree path'])
        self.assertEqual(response.status_code, HttpResponse.status_code)

    @override_flag('education_group_update', active=False)
    def test_detach_case_flag_disabled(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_detach_case_user_not_have_access(self):
        person = PersonFactory()
        self.client.force_login(person.user)
        response = self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/blocks/modal/modal_access_denied.html")

    def test_detach_case_get_with_ajax_success(self):
        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "tree/detach_confirmation_inner.html")

    @mock.patch("program_management.ddd.service.detach_node_service.detach_node")
    @mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group")
    def test_detach_case_post_success(self, mock_permission, mock_service):
        mock_permission.return_value = True
        mock_service.return_value = BusinessValidationMessageList(
            messages=[BusinessValidationMessage('Success', MessageLevel.SUCCESS)]
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

    @mock.patch("base.models.group_element_year.GroupElementYear.delete")
    @mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group")
    def test_detach_when_element_is_in_clipboard(self, mock_permission, mock_delete):
        ElementCache(self.person.user).save_element_selected(
            self.group_element_year.child_branch,
            source_link_id=self.group_element_year.id
        )
        self.client.post(
            self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest', data={'path': self.path_to_detach}
        )
        error_msg = "The clipboard should be cleared if detached element is in clipboard"
        self.assertFalse(ElementCache(self.person.user).cached_data, error_msg)

    @mock.patch("base.models.group_element_year.GroupElementYear.delete")
    @mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group")
    def test_detach_when_clipboard_filled_with_different_detached_element(self, mock_permission, mock_delete):
        element_cached = EducationGroupYearFactory()
        ElementCache(self.person.user).save_element_selected(
            element_cached,
        )
        self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest', data={'path': self.path_to_detach})
        error_msg = "The clipboard should not be cleared if element in clipboard is not the detached element"
        self.assertEqual(ElementCache(self.person.user).cached_data['id'], element_cached.id, error_msg)

    @mock.patch('base.business.event_perms.EventPerm.is_open', return_value=False)
    def test_detach_not_permitted_for_faculty_manager_if_period_closed(self, mock_period_open):
        faculty_manager = FacultyManagerFactory(entity=self.education_group_year.management_entity)
        group_element_year = GroupElementYearFactory(parent=self.group_element_year.parent)
        self.assertFalse(
            faculty_manager.person.user.has_perm('base.can_detach_node', group_element_year.parent)
        )

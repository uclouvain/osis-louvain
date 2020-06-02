##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.auth.models import Permission
from django.http import HttpResponseNotFound, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponse
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

from base.business.education_groups.perms import is_eligible_to_change_education_group_content
from base.models.enums.groups import PROGRAM_MANAGER_GROUP, FACULTY_MANAGER_GROUP
from base.templatetags.education_group import _get_permission
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import CentralManagerForUEFactory, PersonWithPermissionsFactory


@override_flag('education_group_update', active=True)
class TestUp(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.education_group_year = EducationGroupYearFactory(academic_year=cls.academic_year)
        # Create contents of education group years [3 elements]
        cls.group_element_year_1 = GroupElementYearFactory(parent=cls.education_group_year,
                                                           child_branch__academic_year=cls.academic_year)
        cls.group_element_year_2 = GroupElementYearFactory(parent=cls.education_group_year,
                                                           child_branch__academic_year=cls.academic_year)
        cls.group_element_year_3 = GroupElementYearFactory(parent=cls.education_group_year,
                                                           child_branch__academic_year=cls.academic_year)

        cls.person = CentralManagerForUEFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="view_educationgroup"))
        cls.url = reverse(
            "group_element_year_up",
            args=[cls.education_group_year.id, cls.group_element_year_3.id]
        )
        cls.post_valid_data = {}

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_up_case_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url, self.post_valid_data)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    @override_flag('education_group_update', active=False)
    def test_up_case_flag_disabled(self):
        response = self.client.post(self.url, self.post_valid_data)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    @mock.patch("osis_role.contrib.permissions.ObjectPermissionBackend.has_perm")
    def test_up_case_user_not_have_access(self, mock_permission):
        mock_permission.return_value = False
        response = self.client.post(self.url, self.post_valid_data)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    @mock.patch("osis_role.contrib.permissions.ObjectPermissionBackend.has_perm")
    def test_up_case_method_not_allowed(self, mock_permission):
        mock_permission.return_value = True
        response = self.client.get(self.url, data=self.post_valid_data)
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    @mock.patch("program_management.ddd.service.order_link_service.up_link")
    @mock.patch("osis_role.contrib.permissions.ObjectPermissionBackend.has_perm")
    def test_up_case_success(self, mock_permission, mock_up):
        mock_permission.return_value = True
        http_referer = reverse(
            'education_group_content',
            args=[
                self.education_group_year.id,
                self.education_group_year.id,
            ]
        )
        response = self.client.post(self.url, data=self.post_valid_data, follow=True, HTTP_REFERER=http_referer)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTrue(mock_up.called)


class TestOrderingButtons(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.education_group_year = EducationGroupYearFactory(academic_year=cls.academic_year)
        cls.group_element_year = GroupElementYearFactory(
            parent=cls.education_group_year,
            child_branch__academic_year=cls.academic_year
        )

    def test_button_order_disabled_for_program_manager(self):
        program_manager = PersonWithPermissionsFactory(groups=(PROGRAM_MANAGER_GROUP, ))
        context = {'person': program_manager, 'group': self.group_element_year, 'root': None}
        self.assertEqual(_get_permission(context, is_eligible_to_change_education_group_content)[1], 'disabled')

    @mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group")
    @mock.patch("base.business.education_groups.perms._is_year_editable")
    def test_button_order_enabled_for_person_with_both_roles(self, mock_permission, mock_year_editable):
        mock_permission.return_value = True
        mock_year_editable.return_value = True
        person_with_both_roles = PersonWithPermissionsFactory(
            'change_link_data',
            groups=(PROGRAM_MANAGER_GROUP, FACULTY_MANAGER_GROUP)
        )
        context = {'person': person_with_both_roles, 'group': self.group_element_year, 'root': None}
        self.assertEqual(_get_permission(context, is_eligible_to_change_education_group_content)[1], '')


@override_flag('education_group_update', active=True)
class TestDown(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.education_group_year = EducationGroupYearFactory(academic_year=cls.current_academic_year)
        # Create contents of education group years [3 elements]
        cls.group_element_year_1 = GroupElementYearFactory(parent=cls.education_group_year,
                                                           child_branch__academic_year=cls.current_academic_year)
        cls.group_element_year_2 = GroupElementYearFactory(parent=cls.education_group_year,
                                                           child_branch__academic_year=cls.current_academic_year)
        cls.group_element_year_3 = GroupElementYearFactory(parent=cls.education_group_year,
                                                           child_branch__academic_year=cls.current_academic_year)

        cls.person = CentralManagerForUEFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="view_educationgroup"))
        cls.url = reverse(
            "group_element_year_down",
            args=[cls.education_group_year.id, cls.group_element_year_3.id]
        )
        cls.post_valid_data = {}

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_down_case_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url, self.post_valid_data)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    @override_flag('education_group_update', active=False)
    def test_down_case_flag_disabled(self):
        response = self.client.post(self.url, self.post_valid_data)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    @mock.patch("osis_role.contrib.permissions.ObjectPermissionBackend.has_perm")
    def test_down_case_user_not_have_access(self, mock_permission):
        mock_permission.return_value = False
        response = self.client.post(self.url, self.post_valid_data)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    @mock.patch("osis_role.contrib.permissions.ObjectPermissionBackend.has_perm")
    def test_down_case_method_not_allowed(self, mock_permission):
        mock_permission.return_value = True
        response = self.client.get(self.url, data=self.post_valid_data)
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    @mock.patch("program_management.ddd.service.order_link_service.down_link")
    @mock.patch("osis_role.contrib.permissions.ObjectPermissionBackend.has_perm")
    def test_down_case_success(self, mock_permission, mock_down):
        mock_permission.return_value = True
        http_referer = reverse(
            'education_group_content',
            args=[
                self.education_group_year.id,
                self.education_group_year.id,
            ]
        )
        response = self.client.post(self.url, data=self.post_valid_data, follow=True, HTTP_REFERER=http_referer)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTrue(mock_down.called)

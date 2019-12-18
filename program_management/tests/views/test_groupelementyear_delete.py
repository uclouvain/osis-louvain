##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.messages import constants as MSG
from django.contrib.messages import get_messages
from django.http import HttpResponse, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import CentralManagerFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory
from base.utils.cache import ElementCache


@override_flag('education_group_update', active=True)
class TestDetach(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.education_group_year = EducationGroupYearFactory(academic_year=cls.academic_year)
        cls.group_element_year = GroupElementYearFactory(parent=cls.education_group_year,
                                                         child_branch__academic_year=cls.academic_year)
        cls.person = CentralManagerFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse("group_element_year_delete", args=[
            cls.education_group_year.id,
            cls.education_group_year.id,
            cls.group_element_year.id
        ])

    def setUp(self):
        self.client.force_login(self.person.user)
        self.perm_patcher = mock.patch(
            "program_management.business.group_element_years.perms.is_eligible_to_detach_group_element_year",
            return_value=True
        )
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

    def test_edit_case_user_not_logged(self):
        self.client.logout()

        response = self.client.post(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    @override_flag('education_group_update', active=False)
    def test_detach_case_flag_disabled(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_detach_case_user_not_have_access(self):
        self.mocked_perm.return_value = False
        response = self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/blocks/modal/modal_access_denied.html")

    def test_detach_case_get_with_ajax_success(self):
        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "group_element_year/confirm_detach_inner.html")

    @mock.patch("base.models.group_element_year.GroupElementYear.delete")
    @mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group")
    def test_detach_case_post_success(self, mock_permission, mock_delete):
        mock_permission.return_value = True

        response = self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'success': True})
        self.assertEqual(list(get_messages(response.wsgi_request))[0].level, MSG.SUCCESS)
        self.assertTrue(mock_delete.called)

    @mock.patch("base.models.group_element_year.GroupElementYear.delete")
    @mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group")
    def test_detach_when_element_is_in_clipboard(self, mock_permission, mock_delete):
        ElementCache(self.person.user).save_element_selected(
            self.group_element_year.child_branch,
            source_link_id=self.group_element_year.id
        )
        self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        error_msg = "The clipboard should be cleared if detached element is in clipboard"
        self.assertFalse(ElementCache(self.person.user).cached_data, error_msg)

    @mock.patch("base.models.group_element_year.GroupElementYear.delete")
    @mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group")
    def test_detach_when_clipboard_filled_with_different_detached_element(self, mock_permission, mock_delete):
        element_cached = EducationGroupYearFactory()
        ElementCache(self.person.user).save_element_selected(
            element_cached,
        )
        self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        error_msg = "The clipboard should not be cleared if element in clipboard is not the detached element"
        self.assertEqual(ElementCache(self.person.user).cached_data['id'], element_cached.id, error_msg)


@override_flag('education_group_update', active=True)
class TestDetachLearningUnitPrerequisite(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.education_group_year = EducationGroupYearFactory(academic_year=cls.academic_year)
        cls.luy = LearningUnitYearFactory()
        cls.group_element_year_root = GroupElementYearFactory(
            parent__academic_year=cls.academic_year,
            child_branch=cls.education_group_year
        )
        cls.group_element_year = GroupElementYearFactory(
            parent=cls.education_group_year,
            child_branch=None,
            child_leaf=cls.luy
        )
        cls.person = CentralManagerFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse("group_element_year_delete", args=[
            cls.education_group_year.id,
            cls.education_group_year.id,
            cls.group_element_year.id
        ])

    def setUp(self):
        self.client.force_login(self.person.user)
        self.perm_patcher = mock.patch(
            "program_management.business.group_element_years.perms.is_eligible_to_detach_group_element_year",
            return_value=True
        )
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

    def test_detach_case_learning_unit_being_prerequisite(self):
        PrerequisiteItemFactory(
            prerequisite__education_group_year=self.group_element_year_root.parent,
            learning_unit=self.luy.learning_unit
        )

        response = self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.json(), {"error": True})

    def test_detach_case_learning_unit_having_prerequisite(self):
        PrerequisiteItemFactory(
            prerequisite__learning_unit_year=self.luy,
            prerequisite__education_group_year=self.group_element_year_root.parent
        )

        response = self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.json(), {"error": True})

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

from django.http import HttpResponseForbidden, HttpResponse, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_types import GroupType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from base.tests.factories.user import UserFactory
from education_group.views.group.common_read import Tab
from program_management.ddd.domain.node import NodeGroupYear
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory


class TestGroupReadGeneralInformation(TestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearFactory(current=True)
        cls.person = PersonWithPermissionsFactory('view_educationgroup')
        cls.element_group_year = ElementGroupYearFactory(
            group_year__partial_acronym="LTRONC100B",
            group_year__academic_year__year=2018,
            group_year__education_group_type__name=GroupType.COMMON_CORE.name
        )
        EducationGroupVersionFactory(offer__academic_year=cls.element_group_year.group_year.academic_year,
                                     root_group=cls.element_group_year.group_year)
        cls.url = reverse('group_general_information', kwargs={'year': 2018, 'code': 'LTRONC100B'})

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

        self.perm_patcher = mock.patch(
            "education_group.views.group.general_information_read.GroupReadGeneralInformation."
            "have_general_information_tab",
            return_value=True
        )
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

    def test_case_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_case_user_have_not_permission(self):
        self.client.force_login(UserFactory())
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_case_group_not_exists(self):
        dummy_url = reverse('group_general_information', kwargs={'year': 2018, 'code': 'DUMMY100B'})
        response = self.client.get(dummy_url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_case_group_unauthorized_general_information_tab(self):
        with mock.patch(
                "education_group.views.group.general_information_read.GroupReadGeneralInformation."
                "have_general_information_tab",
                return_value=False
        ):
            response = self.client.get(self.url)
            expected_redirect = reverse('group_identification', kwargs={'year': 2018, 'code': 'LTRONC100B'}) + \
                                "?path=" + str(self.element_group_year.pk)
            self.assertRedirects(response, expected_redirect)

    def test_assert_template_used(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group_app/group/general_informations_read.html")

    @mock.patch('education_group.views.serializers.general_information.get_sections', return_value={})
    def test_assert_context_data(self, mock_get_sections):
        response = self.client.get(self.url)

        self.assertEqual(response.context['person'], self.person)
        self.assertEqual(response.context['group_year'], self.element_group_year.group_year)
        expected_update_label_url = reverse('group_general_information_update', args=[
            self.element_group_year.group_year.academic_year.year,
            self.element_group_year.group_year.partial_acronym
        ]) + "?path={}".format(self.element_group_year.id)
        self.assertEqual(response.context['update_label_url'], expected_update_label_url)
        expected_publish_url = reverse(
            'publish_general_information', args=["2018", "LTRONC100B"]
        ) + "?path=" + str(self.element_group_year.pk)
        self.assertEqual(response.context['publish_url'], expected_publish_url)
        self.assertIsInstance(response.context['tree'], str)
        self.assertIsInstance(response.context['node'], NodeGroupYear)
        self.assertFalse(response.context['can_edit_information'])

        self.assertTrue(mock_get_sections.called)
        self.assertDictEqual(response.context['sections'], {})

    def test_assert_active_tabs_is_general_information_and_others_are_not_active(self):
        response = self.client.get(self.url)

        self.assertTrue(response.context['tab_urls'][Tab.GENERAL_INFO]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.IDENTIFICATION]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.CONTENT]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.UTILIZATION]['active'])

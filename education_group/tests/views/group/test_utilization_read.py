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

from django.http import HttpResponseForbidden, HttpResponse, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from base.tests.factories.user import UserFactory
from education_group.views.group.common_read import Tab
from program_management.ddd.domain.node import NodeGroupYear
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory


class TestGroupReadUtilization(TestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearFactory(current=True)
        cls.person = PersonWithPermissionsFactory('view_educationgroup')
        cls.element_group_year = ElementGroupYearFactory(
            group_year__partial_acronym="LTRONC100B",
            group_year__academic_year__year=2018
        )
        EducationGroupVersionFactory(offer__academic_year=cls.element_group_year.group_year.academic_year,
                                     root_group=cls.element_group_year.group_year)
        cls.url = reverse('group_utilization', kwargs={'year': 2018, 'code': 'LTRONC100B'})

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

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
        dummy_url = reverse('group_content', kwargs={'year': 2018, 'code': 'DUMMY100B'})
        response = self.client.get(dummy_url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group_app/group/utilization_read.html")

    @mock.patch('program_management.ddd.service.read.search_tree_versions_using_node_service'
                '.search_tree_versions_using_node', return_value=[])
    def test_assert_context_data(self, mock_tree_service):
        response = self.client.get(self.url)

        self.assertTrue(mock_tree_service.called)
        self.assertEqual(response.context['person'], self.person)
        self.assertEqual(response.context['group_year'], self.element_group_year.group_year)
        self.assertIsInstance(response.context['tree'], str)
        self.assertIsInstance(response.context['node'], NodeGroupYear)
        self.assertIsInstance(response.context['utilization_rows'], List)

    def test_assert_active_tabs_is_utilization_and_others_are_not_active(self):
        response = self.client.get(self.url)

        self.assertTrue(response.context['tab_urls'][Tab.UTILIZATION]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.IDENTIFICATION]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.CONTENT]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.GENERAL_INFO]['active'])

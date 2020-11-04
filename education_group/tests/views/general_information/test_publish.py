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
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.person import PersonWithPermissionsFactory


class TestPublishCommonAdmissionCondition(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory('view_educationgroup')

    def setUp(self) -> None:
        self.publish_service_patcher = mock.patch(
            "education_group.views.general_information.publish."
            "publish_common_admission_conditions_service.publish_common_admission_conditions",
            return_value=None
        )
        self.mocked_publish_service = self.publish_service_patcher.start()
        self.addCleanup(self.publish_service_patcher.stop)

        self.client.force_login(self.person.user)

    def test_case_user_not_logged(self):
        self.client.logout()

        url = reverse('publish_common_master_specialized_admission_condition', kwargs={'year': 2018})
        response = self.client.post(url)
        self.assertRedirects(response, '/login/?next={}'.format(url))

    def test_assert_redirect_on_view_after_refresh_case_master_specialized(self):
        url = reverse('publish_common_master_specialized_admission_condition', kwargs={'year': 2018})

        response = self.client.post(url, {})
        self.assertTrue(self.mocked_publish_service.called)

        expected_redirection = reverse('common_master_specialized_admission_condition', kwargs={'year': 2018})
        self.assertRedirects(response, expected_redirection, fetch_redirect_response=False)

    def test_assert_redirect_on_view_after_refresh_case_master(self):
        url = reverse('publish_common_master_admission_condition', kwargs={'year': 2018})

        response = self.client.post(url, {})
        self.assertTrue(self.mocked_publish_service.called)

        expected_redirection = reverse('common_master_admission_condition', kwargs={'year': 2018})
        self.assertRedirects(response, expected_redirection, fetch_redirect_response=False)

    def test_assert_redirect_on_view_after_refresh_case_aggregate(self):
        url = reverse('publish_common_aggregate_admission_condition', kwargs={'year': 2018})

        response = self.client.post(url, {})
        self.assertTrue(self.mocked_publish_service.called)

        expected_redirection = reverse('common_aggregate_admission_condition', kwargs={'year': 2018})
        self.assertRedirects(response, expected_redirection, fetch_redirect_response=False)

    def test_assert_redirect_on_view_after_refresh_case_bachelor(self):
        url = reverse('publish_common_bachelor_admission_condition', kwargs={'year': 2018})

        response = self.client.post(url, {})
        self.assertTrue(self.mocked_publish_service.called)

        expected_redirection = reverse('common_bachelor_admission_condition', kwargs={'year': 2018})
        self.assertRedirects(response, expected_redirection, fetch_redirect_response=False)


class TestPublishCommonPedagogy(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory('view_educationgroup')
        cls.url = reverse('publish_common_general_information', kwargs={'year': 2018})

    def setUp(self) -> None:
        self.publish_service_patcher = mock.patch(
            "education_group.views.general_information.publish."
            "publish_common_pedagogy_service.publish_common_pedagogy",
            return_value=None
        )
        self.mocked_publish_service = self.publish_service_patcher.start()
        self.addCleanup(self.publish_service_patcher.stop)

        self.client.force_login(self.person.user)

    def test_case_user_not_logged(self):
        self.client.logout()

        response = self.client.post(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_assert_redirect_on_view(self):
        response = self.client.post(self.url, {})
        self.assertTrue(self.mocked_publish_service.called)

        expected_redirection = reverse('common_general_information', kwargs={'year': 2018})
        self.assertRedirects(response, expected_redirection, fetch_redirect_response=False)

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

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from base.tests.factories.user import UserFactory


class RecomputePortalTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.global_ids = ['12348', '565656', '5888']
        self.url = reverse('recompute_tutor_application_portal')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_recompute_portal_without_authentification(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, {'global_ids': self.global_ids})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_recompute_portal_not_valid_http_method(self):
        response = self.client.get(self.url, {'global_ids': self.global_ids})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @mock.patch('attribution.business.application_json.publish_to_portal', side_effect=lambda global_ids: True)
    def test_recompute_portal_success_test_case(self, mock_publish_to_portal):
        response = self.client.post(self.url, {'global_ids': self.global_ids})
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_publish_to_portal.assert_called_with(self.global_ids)

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
from django.http import HttpResponseRedirect, HttpResponse
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from base.tests.factories.person import PersonFactory


class UserListViewTestCase(APITestCase):
    def setUp(self):
        self.user = PersonFactory().user

    def test_user_list_connected(self):
        self.client.force_login(self.user)
        url = reverse('academic_actors_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_user_list_not_connected(self):
        url = reverse('academic_actors_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

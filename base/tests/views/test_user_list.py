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
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.test import TestCase
from rest_framework.reverse import reverse

from base.tests.factories.person import PersonFactory


class UserListViewTestCase(TestCase):

    def setUp(self):
        self.user = PersonFactory().user
        self.permission = Permission.objects.get(codename='can_read_persons_roles')
        self.client.force_login(self.user)

    def test_user_list_forbidden(self):
        url = reverse('academic_actors_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_user_list_with_permission(self):
        url = reverse('academic_actors_list')
        self.user.user_permissions.add(self.permission)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

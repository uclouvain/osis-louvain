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
from http import HTTPStatus
from unittest import mock

from django.http import HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

from base.models.enums import quadrimesters
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import CentralManagerFactory


@override_flag('education_group_update', active=True)
class TestEdit(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year = EducationGroupYearFactory()
        cls.group_element_year = GroupElementYearFactory(parent=cls.education_group_year)
        cls.person = CentralManagerFactory()
        cls.url = reverse(
            "group_element_year_update",
            kwargs={
                "root_id": cls.education_group_year.id,
                "education_group_year_id": cls.education_group_year.id,
                "group_element_year_id": cls.group_element_year.id
            }
        )
        cls.post_valid_data = {'action': 'edit'}

    def setUp(self):
        self.client.force_login(self.person.user)
        self.perm_patcher = mock.patch(
            "base.business.group_element_years.perms.is_eligible_to_create_group_element_year",
            return_value=True
        )
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

    def test_edit_case_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url, self.post_valid_data)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    @override_flag('education_group_update', active=False)
    def test_edit_case_flag_disabled(self):
        response = self.client.post(self.url, self.post_valid_data)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_edit_comment_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "education_group/group_element_year_comment_inner.html")

    def test_edit_comment_get_ajax(self):
        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "education_group/group_element_year_comment_inner.html")

    def test_edit_comment_post(self):
        data = {
            "comment":  """C'est une affaire dangereuse de passer ta porte, Frodon, 
            Tu vas sur la route, et si tu ne retiens pas tes pieds,
            Dieu sait jusqu'où tu pourrais être emporté.""",

            "comment_english": """It's a dangerous business, Frodo, 
            going out your door. You step onto the road, and if you don't keep your feet,
             there's no knowing where you might be swept off to.""",

            "quadrimester_derogation": quadrimesters.Q1,
        }
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        self.group_element_year.refresh_from_db()
        self.assertEqual(self.group_element_year.comment, data['comment'])
        self.assertEqual(self.group_element_year.comment_english, data['comment_english'])
        self.assertEqual(self.group_element_year.quadrimester_derogation, data['quadrimester_derogation'])

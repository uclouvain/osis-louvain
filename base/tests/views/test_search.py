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
from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.forms.search.search_tutor import TutorSearchForm
from base.tests.factories.person import PersonWithPermissionsFactory, PersonFactory
from base.tests.factories.tutor import TutorFactory

NUMBER_TUTORS = 10


class TestSearchTutors(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tutors = [TutorFactory() for _ in range(NUMBER_TUTORS)]
        cls.url = reverse("search_tutors")

        cls.person = PersonWithPermissionsFactory("can_access_learningunit")

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_when_user_not_logged(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_when_user_has_no_right(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_context(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "search/search.html")

        self.assertIsInstance(response.context["form"], TutorSearchForm)

# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.person import PersonFactory


class TestPublish(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

    def test_should_redirect_to_learning_unit_portal_with_updated_cache_url_when_accessed(self):
        code = "LOSIS1452"
        year = 2020
        url = reverse("access_publication", kwargs={"code": code, "year": 2020})
        response = self.client.get(url, follow=False)

        expected_url = settings.LEARNING_UNIT_PORTAL_URL_WITH_UPDATED_CACHE.format(year=year, acronym=code)
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)


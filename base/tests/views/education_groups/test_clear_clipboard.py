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

from django.http import HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse, HttpResponseBadRequest
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import CentralManagerForUEFactory
from base.tests.factories.user import UserFactory
from base.utils.cache import ElementCache


class TestClearClipboard(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("education_group_clear_clipboard")
        cls.central_manager = CentralManagerForUEFactory("view_educationgroup", user__superuser=False)

    def test_when_not_logged(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_without_permission(self):
        an_other_user = UserFactory()
        self.client.force_login(an_other_user)
        response = self.client.post(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_user_with_permission_get_method(self):
        self.client.force_login(self.central_manager.user)
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "method_not_allowed.html")
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    def test_user_with_permission_post_method_not_ajax(self):
        self.client.force_login(self.central_manager.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)

    def test_user_with_permission_post_method_ajax(self):
        self.client.force_login(self.central_manager.user)
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, JsonResponse.status_code)

    def test_clipboard_is_cleared(self):
        self.client.force_login(self.central_manager.user)
        luy = LearningUnitYearFactory()

        element_cache = ElementCache(self.central_manager.user)
        element_cache.save_element_selected(luy)
        self.assertDictEqual(
            element_cache.cached_data,
            {'id': luy.pk, 'modelname': 'base_learningunityear', 'action': ElementCache.ElementCacheAction.COPY.value}
        )

        self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIsNone(element_cache.cached_data)

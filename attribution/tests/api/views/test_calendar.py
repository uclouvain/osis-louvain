##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from attribution.api.views.calendar import ApplicationCoursesCalendarListView
from attribution.calendar.application_courses_calendar import ApplicationCoursesCalendar
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.person import PersonFactory


class ApplicationCoursesCalendarListViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.url = reverse('attribution_api_v1:' + ApplicationCoursesCalendarListView.name)

    def setUp(self):
        self.client.force_authenticate(user=self.person.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_results(self):
        OpenAcademicCalendarFactory(reference=ApplicationCoursesCalendar.event_reference)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json()
        self.assertEqual(len(results), 1)

        self.assertCountEqual(
            list(results[0].keys()),
            ["title", "start_date", "end_date", "authorized_target_year", "is_open"]
        )

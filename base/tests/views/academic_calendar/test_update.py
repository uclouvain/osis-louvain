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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

import mock
from django.http import HttpResponseForbidden
from django.http.response import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse

from base.business.academic_calendar import AcademicEvent
from base.forms.academic_calendar.update import AcademicCalendarUpdateForm
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.person import PersonWithPermissionsFactory, PersonFactory


class TestAcademicCalendarUpdate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.open_event = AcademicEvent(
            id=1,
            title="Candidature en ligne",
            authorized_target_year=2020,
            start_date=datetime.date.today() - datetime.timedelta(days=5),
            end_date=datetime.date.today() + datetime.timedelta(days=5),
            type=AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name
        )
        cls.url = reverse('academic_calendar_update', kwargs={'academic_calendar_id': cls.open_event.id})

    def setUp(self) -> None:
        self.patcher_get_academic_event = mock.patch('base.views.academic_calendar.update.AcademicEventRepository.get')
        self.mock_get_academic_event = self.patcher_get_academic_event.start()
        self.mock_get_academic_event.return_value = self.open_event
        self.addCleanup(self.patcher_get_academic_event.stop)

        self.person = PersonWithPermissionsFactory("can_access_academic_calendar")
        self.client.force_login(self.person.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_user_has_not_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertTemplateUsed(response, "academic_calendar/update_inner.html")

    def test_assert_context_have_keys(self):
        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertIn('academic_event', response.context)
        self.assertIn('form', response.context)

        self.assertIsInstance(response.context['form'], AcademicCalendarUpdateForm)

    def test_assert_initial_form_provided(self):
        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertDictEqual(response.context['form'].initial,  {
            'start_date': self.open_event.start_date,
            'end_date': self.open_event.end_date
        })

    @mock.patch('base.views.academic_calendar.update.AcademicEventRepository.update', return_value=None)
    def test_assert_post_call_update_repository(self, mock_update):
        response = self.client.post(self.url, data={
            'start_date': datetime.date.today(),
            'end_date': ''
        }, follow=False)

        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        self.assertTrue(mock_update.called)

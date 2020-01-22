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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.forms.academic_calendar import AcademicCalendarForm
from base.models.academic_calendar import AcademicCalendar
from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from base.views.academic_calendar import _compute_progress

now = datetime.datetime.now()
today = datetime.date.today()


class AcademicCalendarViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce_in_future(quantity=6)
        cls.academic_calendars = [
            AcademicCalendarFactory(academic_year=cls.academic_years[i])
            for i in range(len(cls.academic_years))
        ]

        cls.academic_calendars[2].reference = academic_calendar_type.TESTING
        cls.academic_calendars[2].save()

        cls.person = PersonWithPermissionsFactory("can_access_academic_calendar", user__superuser=True)
        cls.url = reverse('academic_calendars')

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_academic_calendars(self):
        response = self.client.get(self.url, data={"show_academic_events": "on"})

        self.assertTemplateUsed(response, 'academic_calendar/academic_calendars.html')
        self._compare_academic_calendar_json(response.context, self.academic_calendars[0])

    def test_academic_calendars_search(self):
        response = self.client.get(
            self.url,
            data={'academic_year': self.academic_years[1].id, 'show_academic_events': 'on'}
        )

        self.assertTemplateUsed(response, 'academic_calendar/academic_calendars.html')
        self._compare_academic_calendar_json(response.context, self.academic_calendars[1])

    def test_project_calendars_search(self):
        response = self.client.get(
            self.url,
            data={'academic_year': self.academic_years[2].id, 'show_academic_events': 'on', 'show_project_events': 'on'}
        )

        self.assertTemplateUsed(response, 'academic_calendar/academic_calendars.html')
        self._compare_academic_calendar_json(response.context, self.academic_calendars[2],
                                             category=academic_calendar_type.PROJECT_CATEGORY)

    def _compare_academic_calendar_json(self, context, calendar, category=academic_calendar_type.ACADEMIC_CATEGORY):
        self.assertDictEqual(
            context['academic_calendar_json'],
            {'data': [
                {
                    'color': academic_calendar_type.CALENDAR_TYPES_COLORS.get(calendar.reference, '#337ab7'),
                    'text': calendar.title,
                    'start_date': calendar.start_date.strftime('%d-%m-%Y'),
                    'end_date': calendar.end_date.strftime('%d-%m-%Y'),
                    'progress': _compute_progress(calendar),
                    'id': calendar.id,
                    'category': category,
                }
            ]}
        )

    def test_academic_calendar_read(self):
        url = reverse("academic_calendar_form", args=[self.academic_calendars[1].id])

        response = self.client.get(url)

        self.assertTemplateUsed(response, 'academic_calendar/academic_calendar_form.html')
        self.assertIsInstance(response.context['form'], AcademicCalendarForm)

        data = {
            "academic_year": self.academic_years[1].pk,
            "title": "Academic event",
            "description": "Description of an academic event",
            "start_date": datetime.date.today(),
            "end_date": datetime.date.today() + datetime.timedelta(days=2)
        }

        response = self.client.post(url, data=data)

        self.assertTemplateUsed(response, 'academic_calendar/academic_calendar.html')

    def test_academic_calendar_form_unauthorized(self):
        self.client.logout()
        person = PersonWithPermissionsFactory("can_access_academic_calendar", user__superuser=False)
        self.client.force_login(person.user)
        url = reverse("academic_calendar_form", args=[self.academic_calendars[1].id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')


class AcademicCalendarDeleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.person = PersonFactory(user__superuser=True)
        cls.academic_calendar = AcademicCalendarFactory(academic_year=cls.academic_year)
        cls.url = reverse('academic_calendar_delete', kwargs={'pk': cls.academic_calendar.pk})

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_academic_calendar_delete_not_superuser(self):
        person_not_superuser = PersonFactory()
        self.client.force_login(person_not_superuser.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_academic_calendar_delete(self):
        response = self.client.post(self.url)

        self.assertRedirects(response, reverse('academic_calendars'))

        with self.assertRaises(AcademicCalendar.DoesNotExist):
            self.academic_calendar.refresh_from_db()

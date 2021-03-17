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

import attr
import mock
from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.business.academic_calendar import AcademicEvent
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from base.views.academic_calendar.read import AcademicCalendarFilter, AcademicCalendarsView
from education_group.templatetags.academic_year_display import display_as_academic_year


class TestAcademicCalendarsView(TestCase):
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
        cls.url = reverse('academic_calendars')

    def setUp(self) -> None:
        self.patcher_get_academic_events = mock.patch(
            'base.views.academic_calendar.read.AcademicEventRepository.get_academic_events'
        )
        self.mock_get_academic_events = self.patcher_get_academic_events.start()
        self.mock_get_academic_events.return_value = [self.open_event]
        self.addCleanup(self.patcher_get_academic_events.stop)

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
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "academic_calendar/academic_calendars.html")

    def test_assert_context_have_keys(self):
        response = self.client.get(self.url)

        self.assertIn('filter', response.context)
        self.assertIn('gantt_rows', response.context)

        self.assertIsInstance(response.context['filter'], AcademicCalendarFilter)

    def test_assert_default_value_case_no_research(self):
        current_academic_year = AcademicYearFactory(current=True)
        response = self.client.get(self.url)

        form = response.context['filter'].form
        self.assertDictEqual(form.data, {
            'event_type': [
                AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name,
                AcademicCalendarTypes.EXAM_ENROLLMENTS.name,
                AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name,
                AcademicCalendarTypes.SCORES_EXAM_DIFFUSION.name,
                AcademicCalendarTypes.COURSE_ENROLLMENT.name,
                AcademicCalendarTypes.SUMMARY_COURSE_SUBMISSION.name,
                AcademicCalendarTypes.SUMMARY_COURSE_SUBMISSION_FORCE_MAJEURE.name,
                AcademicCalendarTypes.EDUCATION_GROUP_EDITION.name,
                AcademicCalendarTypes.DELIBERATION.name,
                AcademicCalendarTypes.DISSERTATION_SUBMISSION.name,
            ],
            'from_date': current_academic_year.start_date,
            'to_date': current_academic_year.end_date
        })

    def test_assert_gantt_rows_formated(self):
        response = self.client.get(self.url)

        self.assertEqual(len(response.context['gantt_rows']), 2)

        # Main row
        expected_main_row = {
            'id': AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name,
            'text': AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.value,
            'type': 'project',
            'render': 'split',
            'color': 'transparent'
        }
        self.assertEqual(response.context['gantt_rows'][0], expected_main_row)

        # Subrow
        expected_subrow = {
            'text': display_as_academic_year(self.open_event.authorized_target_year),
            'tooltip_text': "{} ({})".format(
                self.open_event.title, display_as_academic_year(self.open_event.authorized_target_year)
            ),
            'start_date': self.open_event.start_date.strftime('%d-%m-%Y'),
            'end_date': self.open_event.end_date.strftime('%d-%m-%Y'),
            'parent': AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name,
            'update_url': reverse('academic_calendar_update', kwargs={'academic_calendar_id': self.open_event.id})
        }
        self.assertEqual(response.context['gantt_rows'][1], expected_subrow)

    def test_assert_get_gantt_row_case_unspecified_end_date(self):
        self.mock_get_academic_events.return_value = [
            attr.evolve(self.open_event, end_date=None)
        ]

        response = self.client.get(self.url)
        self.assertEqual(len(response.context['gantt_rows']), 2)

        # Subrow - validation
        expected_subrow = {
            'text': display_as_academic_year(self.open_event.authorized_target_year),
            'tooltip_text': "{} ({})".format(
                self.open_event.title, display_as_academic_year(self.open_event.authorized_target_year)
            ),
            'start_date': self.open_event.start_date.strftime('%d-%m-%Y'),
            'end_date': AcademicCalendarsView.indefinitely_date_value,
            'parent': AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name,
            'update_url': reverse('academic_calendar_update', kwargs={'academic_calendar_id': self.open_event.id})
        }
        self.assertEqual(response.context['gantt_rows'][1], expected_subrow)

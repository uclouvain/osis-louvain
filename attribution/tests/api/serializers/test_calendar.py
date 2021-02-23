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
import datetime

from django.test import TestCase

from attribution.api.serializers.calendar import ApplicationCourseCalendarSerializer
from base.business.event_perms import AcademicEvent
from base.models.enums.academic_calendar_type import AcademicCalendarTypes


class ApplicationCourseCalendarSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event_open = AcademicEvent(
            id=10,
            title="Candidature en ligne",
            authorized_target_year=2020,
            start_date=datetime.date.today() - datetime.timedelta(days=2),
            end_date=datetime.date.today() + datetime.timedelta(days=10),
            type=AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name
        )
        cls.serializer = ApplicationCourseCalendarSerializer(cls.event_open)

    def test_contains_expected_fields(self):
        expected_fields = [
            'title',
            'start_date',
            'end_date',
            'authorized_target_year',
            'is_open',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_ensure_is_open_correctly_computed(self):
        self.assertEquals(self.serializer.data['is_open'], self.event_open.is_open_now())

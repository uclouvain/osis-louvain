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
from decimal import Decimal
from types import SimpleNamespace

import mock
from django.test import TestCase, override_settings

from attribution.api.serializers.attribution import AttributionSerializer
from attribution.calendar.access_schedule_calendar import AccessScheduleCalendar
from attribution.models.enums.function import Functions
from base.business.academic_calendar import AcademicEvent
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.learning_container_year_types import LearningContainerYearType


@override_settings(
    LEARNING_UNIT_PORTAL_URL="https://dummy_url.be/cours-{year}-{code}",
    SCHEDULE_APP_URL="https://schedule_dummy.uclouvain.be/{code}"
)
class AttributionSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.attribution_obj = SimpleNamespace(
            allocation_id="265656",  # Technical ID for making a match with data in EPC. Remove after refactoring...
            code="LDROI1001",
            type=LearningContainerYearType.COURSE.name,
            title_fr="Introduction aux droits Partie I",
            title_en="Introduction aux droits Partie I",
            year=2020,
            credits=Decimal("15.5"),
            start_year=2015,
            function=Functions.COORDINATOR.name,
        )

        cls.academic_event = AcademicEvent(
            id=15,
            title="Accès horaire ADE",
            authorized_target_year=2020,
            start_date=datetime.date.today() - datetime.timedelta(days=2),
            end_date=datetime.date.today() + datetime.timedelta(days=10),
            type=AcademicCalendarTypes.ACCESS_SCHEDULE_CALENDAR.name
        )
        # Fake remote data from EPC API Call
        cls.attributions_charges = [
            {
                'allocationId': cls.attribution_obj.allocation_id,
                'allocationChargePractical': '10.5',
                'allocationChargeLecturing': '15.0',
                'learningUnitCharge': '55.5',
            }
        ]

        cls.serializer = AttributionSerializer(cls.attribution_obj, context={
            'access_schedule_calendar': AccessScheduleCalendar(),
            'attribution_charges': cls.attributions_charges
        })

    def setUp(self) -> None:
        self.patcher_get_academic_events = mock.patch(
            'attribution.api.views.attribution.AccessScheduleCalendar._get_academic_events',
            new_callable=mock.PropertyMock
        )
        self.mock_get_academic_events = self.patcher_get_academic_events.start()
        self.mock_get_academic_events.return_value = [self.academic_event]
        self.addCleanup(self.patcher_get_academic_events.stop)

    def test_contains_expected_fields(self):
        expected_fields = [
            'code',
            'title_fr',
            'title_en',
            'year',
            'type',
            'type_text',
            'credits',
            'start_year',
            'function',
            'function_text',
            'lecturing_charge',
            'practical_charge',
            'total_learning_unit_charge',
            'links'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_ensure_function_text_correctly_computed(self):
        self.assertEquals(self.serializer.data['function_text'], Functions.COORDINATOR.value)

    def test_ensure_type_text_correctly_computed(self):
        self.assertEquals(self.serializer.data['type_text'], LearningContainerYearType.COURSE.value)

    def test_ensure_catalog_app_url_correctly_computed(self):
        expected_url = "https://dummy_url.be/cours-{year}-{code}".format(
            year=self.attribution_obj.year,
            code=self.attribution_obj.code
        )
        self.assertEquals(self.serializer.data['links']['catalog'], expected_url)

    def test_ensure_schedule_app_url_correctly_computed_case_calendar_opened(self):
        expected_url = "https://schedule_dummy.uclouvain.be/{code}".format(
            code=self.attribution_obj.code
        )
        self.assertEquals(self.serializer.data['links']['schedule'], expected_url)

    def test_ensure_lecturing_charge_correctly_found(self):
        expected_lecturing_charge = "15.0"
        self.assertEquals(self.serializer.data['lecturing_charge'], expected_lecturing_charge)

    def test_ensure_practical_charge_correctly_found(self):
        expected_practical_charge = "10.5"
        self.assertEquals(self.serializer.data['practical_charge'], expected_practical_charge)

    def test_ensure_total_learning_unit_charge_correctly_found(self):
        expected_total_learning_unit_charge = "55.5"
        self.assertEquals(self.serializer.data['total_learning_unit_charge'], expected_total_learning_unit_charge)

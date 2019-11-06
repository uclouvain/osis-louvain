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
from django.test import TestCase

from base.forms.entity_calendar import EntityCalendarEducationalInformationForm
from base.models.entity_calendar import EntityCalendar
from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.entity_version import EntityVersionFactory


class TestEntityCalendarEducationalInformationForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_calendar = AcademicCalendarFactory(academic_year=create_current_academic_year(),
                                                        reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)
    def test_fields(self):
        entity_version = EntityVersionFactory()
        entity_version.refresh_from_db()
        form = EntityCalendarEducationalInformationForm(entity_version)
        expected_fields = ["start_date", "end_date"]
        actual_fields = list(form.fields.keys())
        self.assertListEqual(expected_fields, actual_fields)

    def test_save_entity_calendar(self):
        entity_version = EntityVersionFactory()
        entity_version.refresh_from_db()
        entity = entity_version.entity

        form = EntityCalendarEducationalInformationForm(entity_version, {"start_date": "05/03/2018", "end_date": "06/03/2018"})

        self.assertTrue(form.is_valid())
        self.assertFalse(EntityCalendar.objects.all().exists())

        form.save_entity_calendar(entity)

        self.assertTrue(EntityCalendar.objects.get(entity=entity, academic_calendar=self.academic_calendar))

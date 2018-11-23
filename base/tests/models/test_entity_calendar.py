##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils import timezone

from base.models import entity_calendar
from base.models.entity_calendar import find_by_entity_and_reference
from base.models.enums.academic_calendar_type import SUMMARY_COURSE_SUBMISSION, EXAM_ENROLLMENTS
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.entity_calendar import EntityCalendarFactory
from base.tests.factories.entity_version import EntityVersionFactory


class TestFindByReferenceForCurrentAcademicYear(TestCase):
    @classmethod
    def setUpTestData(cls):
        current_academic_year = create_current_academic_year()
        previous_academic_year = AcademicYearFactory(year=current_academic_year.year-1)

        cls.current_entity_calendar = EntityCalendarFactory(academic_calendar__academic_year=current_academic_year,
                                                            academic_calendar__reference=SUMMARY_COURSE_SUBMISSION)
        previous_entity_calendar = EntityCalendarFactory(academic_calendar__academic_year=previous_academic_year,
                                                         academic_calendar__reference=SUMMARY_COURSE_SUBMISSION,
                                                         entity=cls.current_entity_calendar.entity)

    def test_when_no_data_match_criteria(self):
        entity_calendar_obj = find_by_entity_and_reference(
            self.current_entity_calendar.entity.id, EXAM_ENROLLMENTS)
        self.assertIsNone(entity_calendar_obj)

    def test_find_for_current_academic_year(self):
        entity_calendar_obj = find_by_entity_and_reference(
            self.current_entity_calendar.entity.id,
            SUMMARY_COURSE_SUBMISSION
        )
        self.assertEqual(entity_calendar_obj, self.current_entity_calendar)


class TestBuildCalendarByEntity(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()
        cls.ac_calendar = AcademicCalendarFactory(academic_year=cls.academic_year, reference=SUMMARY_COURSE_SUBMISSION)

        # Create structure entity
        cls.entity_ssh = EntityVersionFactory(acronym='SSH', parent=None)
        cls.entity_lsm = EntityVersionFactory(acronym='LSM', parent=cls.entity_ssh.entity)
        cls.entity_clsm = EntityVersionFactory(acronym='CLSM', parent=cls.entity_lsm.entity)

        cls.entity_sst = EntityVersionFactory(acronym='SST', parent=None)
        cls.entity_drt = EntityVersionFactory(acronym='DRT', parent=cls.entity_sst.entity)
        cls.entity_agro = EntityVersionFactory(acronym='AGRO', parent=cls.entity_sst.entity)

    def test_build_calendar_by_entity_no_entity_calendars(self):
        entity_calendar_computed = entity_calendar.build_calendar_by_entities(self.academic_year,
                                                                              SUMMARY_COURSE_SUBMISSION)
        default_date = {'start_date': self.ac_calendar.start_date, 'end_date': self.ac_calendar.end_date}
        # Check on SSH node
        self.assertDictEqual(entity_calendar_computed[self.entity_ssh.entity.id], default_date)
        self.assertDictEqual(entity_calendar_computed[self.entity_lsm.entity.id], default_date)
        self.assertDictEqual(entity_calendar_computed[self.entity_clsm.entity.id], default_date)
        # Check on SST node
        self.assertDictEqual(entity_calendar_computed[self.entity_sst.entity.id], default_date)
        self.assertDictEqual(entity_calendar_computed[self.entity_drt.entity.id], default_date)
        self.assertDictEqual(entity_calendar_computed[self.entity_agro.entity.id], default_date)

    def test_build_calendar_by_entity_have_entity_calendars_on_leaf_structure(self):
        agro_date = {
            'start_date': timezone.now() - timezone.timedelta(days=5),
            'end_date': timezone.now() + timezone.timedelta(days=20)
        }
        lsm_date = {
            'start_date': timezone.now() - timezone.timedelta(days=40),
            'end_date': timezone.now() + timezone.timedelta(days=100)
        }
        EntityCalendarFactory(academic_calendar=self.ac_calendar, entity=self.entity_agro.entity, **agro_date)
        EntityCalendarFactory(academic_calendar=self.ac_calendar, entity=self.entity_lsm.entity, **lsm_date)

        entity_calendar_computed = entity_calendar.build_calendar_by_entities(self.academic_year,
                                                                              SUMMARY_COURSE_SUBMISSION)
        default_date = {'start_date': self.ac_calendar.start_date, 'end_date': self.ac_calendar.end_date}
        # Check on SSH node
        self.assertDictEqual(entity_calendar_computed[self.entity_ssh.entity.id], default_date)
        self.assertDictEqual(entity_calendar_computed[self.entity_lsm.entity.id], _convert_datetime_to_date(lsm_date))
        self.assertDictEqual(entity_calendar_computed[self.entity_clsm.entity.id], _convert_datetime_to_date(lsm_date))
        # Check on SST node
        self.assertDictEqual(entity_calendar_computed[self.entity_sst.entity.id], default_date)
        self.assertDictEqual(entity_calendar_computed[self.entity_drt.entity.id], default_date)
        self.assertDictEqual(entity_calendar_computed[self.entity_agro.entity.id], _convert_datetime_to_date(agro_date))

    def test_build_calendar_by_entity_have_entity_calendars_on_parent_structure(self):
        sst_date = {
            'start_date': timezone.now() - timezone.timedelta(days=5),
            'end_date': timezone.now() + timezone.timedelta(days=20)
        }
        EntityCalendarFactory(academic_calendar=self.ac_calendar, entity=self.entity_sst.entity, **sst_date)

        entity_calendar_computed = entity_calendar.build_calendar_by_entities(self.academic_year,
                                                                              SUMMARY_COURSE_SUBMISSION)
        default_date = {'start_date': self.ac_calendar.start_date, 'end_date': self.ac_calendar.end_date}
        # Check on SSH node
        self.assertDictEqual(entity_calendar_computed[self.entity_ssh.entity.id], default_date)
        self.assertDictEqual(entity_calendar_computed[self.entity_lsm.entity.id], default_date)
        self.assertDictEqual(entity_calendar_computed[self.entity_clsm.entity.id], default_date)
        # Check on SST node
        self.assertDictEqual(entity_calendar_computed[self.entity_sst.entity.id], _convert_datetime_to_date(sst_date))
        self.assertDictEqual(entity_calendar_computed[self.entity_drt.entity.id], _convert_datetime_to_date(sst_date))
        self.assertDictEqual(entity_calendar_computed[self.entity_agro.entity.id], _convert_datetime_to_date(sst_date))

    def test_find_interval_dates_for_entity(self):
        expected_date = {'start_date': self.ac_calendar.start_date, 'end_date': self.ac_calendar.end_date}
        result = entity_calendar.find_interval_dates_for_entity(self.academic_year, SUMMARY_COURSE_SUBMISSION,
                                                                self.entity_ssh.entity)
        self.assertDictEqual(result, expected_date)

    def test_find_interval_dates_for_entity_with_a_parent_entity_calendar(self):
        sst_date = {
            'start_date': timezone.now() - timezone.timedelta(days=5),
            'end_date': timezone.now() + timezone.timedelta(days=20)
        }
        EntityCalendarFactory(academic_calendar=self.ac_calendar, entity=self.entity_sst.entity, **sst_date)

        expected_date = _convert_datetime_to_date(sst_date)
        result = entity_calendar.find_interval_dates_for_entity(self.academic_year, SUMMARY_COURSE_SUBMISSION,
                                                                self.entity_drt.entity)
        self.assertDictEqual(result, expected_date)


def _convert_datetime_to_date(interval_date):
    interval_date_converted = {
        'start_date': interval_date['start_date'].date(),
        'end_date': interval_date['end_date'].date()
    }
    return interval_date_converted

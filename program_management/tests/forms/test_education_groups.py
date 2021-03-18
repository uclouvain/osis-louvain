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
from django.test import TestCase

from base.models.enums import education_group_categories
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from program_management.forms.education_groups import GroupFilter


class TestGroupFilter(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce(number_past=2, number_future=5)

    def test_ensure_academic_year_initial_value_case_no_education_group_switch_calendar_opened(self):
        filter = GroupFilter()
        self.assertIsNone(filter.form['academic_year'].initial)

    def test_ensure_academic_year_initial_value_case_one_education_group_switch_calendar_opened(self):
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_SWITCH.name,
            data_year=self.academic_years[2]
        )

        filter = GroupFilter()
        self.assertEqual(filter.form['academic_year'].initial, self.academic_years[2])

    def test_ensure_academic_year_initial_value_case_multiple_education_group_switch_calendar_opened(self):
        for academic_year in self.academic_years[:2]:
            OpenAcademicCalendarFactory(
                reference=AcademicCalendarTypes.EDUCATION_GROUP_SWITCH.name,
                data_year=academic_year
            )

        filter = GroupFilter()
        self.assertEqual(filter.form['academic_year'].initial, self.academic_years[0])

    def test_ensure_category_initial_value(self):
        filter = GroupFilter()
        self.assertEqual(filter.form.fields["category"].initial, education_group_categories.TRAINING)

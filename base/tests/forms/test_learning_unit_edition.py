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

from base.business.learning_units.edition import get_next_academic_years
from base.forms.learning_unit.edition import LearningUnitDailyManagementEndDateForm
from base.forms.utils.choice_field import NO_PLANNED_END_DISPLAY
from base.models.academic_year import AcademicYear
from base.models.enums import learning_unit_year_periodicity, learning_unit_year_subtypes, learning_container_year_types
from base.tests.factories.academic_calendar import generate_learning_unit_edition_calendars
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import LearningUnitsMixin
from base.tests.factories.person import CentralManagerFactory


class TestLearningUnitEditionForm(TestCase, LearningUnitsMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.setup_academic_years()
        cls.learning_unit = cls.setup_learning_unit(
            start_year=cls.starting_academic_year)
        cls.learning_container_year = cls.setup_learning_container_year(
            academic_year=cls.starting_academic_year,
            container_type=learning_container_year_types.COURSE
        )
        cls.learning_unit_year = cls.setup_learning_unit_year(
            academic_year=cls.starting_academic_year,
            learning_unit=cls.learning_unit,
            learning_container_year=cls.learning_container_year,
            learning_unit_year_subtype=learning_unit_year_subtypes.FULL,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )
        cls.person_central = CentralManagerFactory()
        generate_learning_unit_edition_calendars(cls.list_of_academic_years)

    def test_edit_end_date_send_dates_with_end_date_not_defined(self):
        form = LearningUnitDailyManagementEndDateForm(
            None, learning_unit_year=self.learning_unit_year, person=self.person_central)
        self.assertEqual(list(form.fields['academic_year'].queryset), self.list_of_academic_years_after_now)
        self.assertFalse(form.fields['academic_year'].required)
        self.assertEqual(NO_PLANNED_END_DISPLAY, form.fields['academic_year'].empty_label)

    def test_edit_end_date_send_dates_with_end_date_defined(self):
        self.learning_unit.end_year = self.last_academic_year
        form = LearningUnitDailyManagementEndDateForm(
            None, learning_unit_year=self.learning_unit_year, person=self.person_central)
        self.assertEqual(list(form.fields['academic_year'].queryset), self.list_of_academic_years_after_now)
        self.assertFalse(form.fields['academic_year'].required)
        self.assertEqual(NO_PLANNED_END_DISPLAY, form.fields['academic_year'].empty_label)

    def test_edit_end_date_send_dates_with_end_date_of_learning_unit_inferior_to_current_academic_year(self):
        self.learning_unit.end_year = self.oldest_academic_year
        form = LearningUnitDailyManagementEndDateForm(
            None, learning_unit_year=self.learning_unit_year, person=self.person_central)
        self.assertEqual(form.fields['academic_year'].disabled, True)
        self.assertFalse(form.fields['academic_year'].required)
        self.assertEqual(NO_PLANNED_END_DISPLAY, form.fields['academic_year'].empty_label)

    def test_edit_end_date(self):
        self.learning_unit.end_year = self.last_academic_year
        form_data = {"academic_year": self.starting_academic_year.pk}
        form = LearningUnitDailyManagementEndDateForm(
            form_data, learning_unit_year=self.learning_unit_year, person=self.person_central)
        self.assertFalse(form.fields['academic_year'].required)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['academic_year'], self.starting_academic_year)
        self.assertEqual(NO_PLANNED_END_DISPLAY, form.fields['academic_year'].empty_label)

    def test_get_next_academic_years(self):
        max_adjournment_year = AcademicYear.objects.max_adjournment().year
        learning_unit_without_end_year = self.setup_learning_unit(self.starting_academic_year)
        learning_unit_with_end_year = self.setup_learning_unit(self.starting_academic_year,
                                                               AcademicYearFactory(year=max_adjournment_year - 1))
        cases = [
            {"name": "without_end_year",
             "learning_unit": learning_unit_without_end_year,
             "last_year": max_adjournment_year,
             "expected_result": 0,
             "expected_queryset": AcademicYear.objects.none()
             },
            {"name": "with_end_year",
             "learning_unit": learning_unit_with_end_year,
             "last_year": max_adjournment_year,
             "expected_result": 1,
             "expected_queryset": AcademicYear.objects.filter(year=max_adjournment_year).order_by('year')
             },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                result = get_next_academic_years(case["learning_unit"], case["last_year"])
                self.assertEqual(case["expected_result"], result.count(), result)
                self.assertEqual(set(case["expected_queryset"]), set(result))

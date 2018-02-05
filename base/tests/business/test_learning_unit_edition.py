##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from datetime import datetime

from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from base.business.learning_units.edition import edit_learning_unit_end_date
from base.models import academic_year
from base.models.entity_component_year import EntityComponentYear
from base.models.entity_container_year import EntityContainerYear
from base.models.enums import learning_unit_year_subtypes, learning_unit_periodicity, learning_container_year_types, \
    attribution_procedure
from base.models.learning_class_year import LearningClassYear
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_component import LearningUnitComponent
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.business.learning_units import LearningUnitsMixin
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_component_year import EntityComponentYearFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from base.tests.factories.learning_unit_component import LearningUnitComponentFactory


class TestLearningUnitEdition(TestCase, LearningUnitsMixin):
    """
    General cases :

        The start date of the learning unit is greater than current academic year
        Only test the ANNUAL periodicity (the BIENNAL periodicity is covered later on)
        The new end date of the learning unit is greater than old end date (creation)
        01. test_edit_learning_unit_full_annual_end_date_gt_old_end_date_with_start_date_gt_now
        02. test_edit_learning_unit_partim_annual_end_date_gt_old_end_date_with_start_date_gt_now

        The start date of the learning unit is less than current academic year
        The new end date of the learning unit is greater than old end date (creation)
        03. test_edit_learning_unit_full_annual_end_date_gt_old_end_date_with_start_date_lt_now
        04. test_edit_learning_unit_full_odd_end_date_gt_old_end_date_with_start_date_lt_now
        05. test_edit_learning_unit_full_even_end_date_gt_old_end_date_with_start_date_lt_now
        06. test_edit_learning_unit_partim_annual_end_gt_old_end_date_date_with_start_date_lt_now

        The new end date of the learning unit is none (creation)
        07. test_edit_learning_unit_full_annual_end_date_is_none_with_start_date_lt_now
        08. test_edit_learning_unit_partim_annual_end_date_is_none_with_start_date_lt_now
        09. test_edit_learning_unit_partim_annual_end_date_is_none_with_start_date_lt_now_with_error

        The new end date of the learning unit is less than old end date (deletion)
        10. test_edit_learning_unit_full_annual_end_date_lt_old_end_date_with_start_date_lt_now
        11. test_edit_learning_unit_full_odd_end_date_lt_old_end_date_with_start_date_lt_now
        12. test_edit_learning_unit_full_even_end_date_lt_old_end_date_with_start_date_lt_now
        13. test_edit_learning_unit_partim_annual_end_date_lt_old_end_date_with_start_date_lt_now
    """

    def setUp(self):
        super().setUp()
        self.setup_academic_years()
        self.learning_container_year_course = self.setup_learning_container_year(
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.COURSE
        )
        self.number_classes = 5
        self.entity_version = EntityVersionFactory(start_date=datetime.now(), end_date=datetime(3000, 1, 1))
        self.entity = self.entity_version.entity

    def test_edit_learning_unit_full_annual_end_date_gt_old_end_date_with_start_date_gt_now(self):
        start_year = self.current_academic_year.year + 1
        end_year = self.current_academic_year.year + 3
        expected_end_year = end_year+2
        list_of_expected_learning_unit_years = list(range(start_year, expected_end_year+1))

        learning_unit_full_annual = self.setup_learning_unit(
            start_year=start_year,
            end_year=end_year,
        )

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual
        )

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(expected_end_year)

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit()
        self.assertEqual(list_of_learning_unit_years, list_of_expected_learning_unit_years)

    def test_edit_learning_unit_partim_annual_end_date_gt_old_end_date_with_start_date_gt_now(self):
        start_year_full = self.current_academic_year.year + 1
        end_year_full = self.current_academic_year.year + 6

        start_year_partim = self.current_academic_year.year + 2
        end_year_partim = self.current_academic_year.year + 3
        excepted_end_year_partim = end_year_partim+2

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)
        learning_unit_partim_annual = self.setup_learning_unit(start_year=start_year_partim, end_year=end_year_partim)

        self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )

        list_of_expected_learning_unit_years_full = list(range(start_year_full, end_year_full+1))
        list_of_expected_learning_unit_years_partim = list(range(start_year_partim, excepted_end_year_partim+1))

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(excepted_end_year_partim)

        edit_learning_unit_end_date(learning_unit_partim_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years_full = _get_list_years_learning_unit(learning_unit_year_subtypes.FULL)
        list_of_learning_unit_years_partim = _get_list_years_learning_unit(learning_unit_year_subtypes.PARTIM)

        self.assertEqual(len(list_of_learning_unit_years_full), len(list_of_expected_learning_unit_years_full))
        self.assertEqual(list_of_learning_unit_years_partim, list_of_expected_learning_unit_years_partim)

    def test_edit_learning_unit_full_annual_end_date_gt_old_end_date_with_start_date_lt_now(self):
        start_year_full = self.current_academic_year.year - 1
        end_year_full = self.current_academic_year.year + 1
        expected_end_year_full = end_year_full + 2

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual
        )

        list_of_expected_learning_unit_years = list(range(start_year_full, expected_end_year_full+1))
        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(expected_end_year_full)

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit(learning_unit_year_subtypes.FULL)
        self.assertEqual(list_of_learning_unit_years, list_of_expected_learning_unit_years)

    def test_edit_learning_unit_full_odd_end_date_gt_old_end_date_with_start_date_lt_now(self):
        start_year = self.current_academic_year.year - 2
        end_year = self.current_academic_year.year + 2
        expected_end_year_full = end_year + 2

        learning_unit_full_annual = self.setup_learning_unit(
            start_year=start_year,
            end_year=end_year,
            periodicity=learning_unit_periodicity.BIENNIAL_ODD
        )

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual
        )

        list_of_expected_learning_unit_years = []
        for learning_unit_year in list(LearningUnitYear.objects.all()):
            list_of_expected_learning_unit_years.append(learning_unit_year.academic_year.year)
        if self.current_academic_year.year % 2:
            list_of_expected_learning_unit_years.append(learning_unit_full_annual.end_year + 2)
        else:
            list_of_expected_learning_unit_years.append(learning_unit_full_annual.end_year + 1)

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(expected_end_year_full)

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit()
        self.assertEqual(list_of_learning_unit_years, sorted(list_of_expected_learning_unit_years))

    def test_edit_learning_unit_full_even_end_date_gt_old_end_date_with_start_date_lt_now(self):
        start_year = self.current_academic_year.year - 2
        end_year = self.current_academic_year.year + 2
        expected_end_year = end_year + 2
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=start_year,
            end_year=end_year,
            periodicity=learning_unit_periodicity.BIENNIAL_EVEN
        )

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual
        )

        list_of_expected_learning_unit_years = []
        for learning_unit_year in list(LearningUnitYear.objects.all()):
            list_of_expected_learning_unit_years.append(learning_unit_year.academic_year.year)
        if self.current_academic_year.year % 2:
            list_of_expected_learning_unit_years.append(learning_unit_full_annual.end_year + 1)
        else:
            list_of_expected_learning_unit_years.append(learning_unit_full_annual.end_year + 2)

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(expected_end_year)

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit()
        self.assertEqual(list_of_learning_unit_years, sorted(list_of_expected_learning_unit_years))

    def test_edit_learning_unit_partim_annual_end_gt_old_end_date_date_with_start_date_lt_now(self):
        start_year_full = self.current_academic_year.year - 1
        end_year_full = self.current_academic_year.year + 3

        start_year_partim = self.current_academic_year.year - 1
        end_year_partim = self.current_academic_year.year + 1
        excepted_end_year_partim = end_year_partim+2

        learning_unit_full_annual = self.setup_learning_unit(
            start_year=start_year_full,
            end_year=end_year_full,
        )
        learning_unit_partim_annual = self.setup_learning_unit(
            start_year=start_year_partim,
            end_year=end_year_partim,
        )

        list_of_learning_unit_years_annual = self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )

        list_of_expected_learning_unit_years_full = []
        list_of_expected_learning_unit_years_partim = []
        for learning_unit_year_expected in list_of_learning_unit_years_annual:
            if learning_unit_year_expected.subtype == learning_unit_year_subtypes.PARTIM:
                list_of_expected_learning_unit_years_partim.append(learning_unit_year_expected.academic_year.year)
            else:
                list_of_expected_learning_unit_years_full.append(learning_unit_year_expected.academic_year.year)
        list_of_expected_learning_unit_years_partim.append(learning_unit_partim_annual.end_year + 1)
        list_of_expected_learning_unit_years_partim.append(learning_unit_partim_annual.end_year + 2)

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(excepted_end_year_partim)

        edit_learning_unit_end_date(learning_unit_partim_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years_full = _get_list_years_learning_unit(subtype=learning_unit_year_subtypes.FULL)
        list_of_learning_unit_years_partim = _get_list_years_learning_unit(subtype=learning_unit_year_subtypes.PARTIM)

        self.assertEqual(list_of_learning_unit_years_full, list_of_expected_learning_unit_years_full)
        self.assertEqual(list_of_learning_unit_years_partim, list_of_expected_learning_unit_years_partim)

    def test_edit_learning_unit_full_annual_end_date_is_none_with_start_date_lt_now(self):
        start_year = self.current_academic_year.year - 1
        end_year = self.current_academic_year.year + 4
        expected_end_year = end_year + 2
        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year, end_year=end_year)

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual
        )

        list_of_expected_learning_unit_years = list(range(start_year, expected_end_year+1))
        academic_year_of_new_end_date = None

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit()
        self.assertEqual(list_of_learning_unit_years, list_of_expected_learning_unit_years)

    def test_edit_learning_unit_partim_annual_end_date_is_none_with_start_date_lt_now(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.current_academic_year.year - 1,
            end_year=self.current_academic_year.year + 6,
        )
        learning_unit_partim_annual = self.setup_learning_unit(
            start_year=self.current_academic_year.year - 1,
            end_year=self.current_academic_year.year + 4,
        )

        list_of_learning_unit_years_annual = self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )

        list_of_expected_learning_unit_years_full = []
        list_of_expected_learning_unit_years_partim = []
        for learning_unit_year_expected in list_of_learning_unit_years_annual:
            if learning_unit_year_expected.subtype == learning_unit_year_subtypes.PARTIM:
                list_of_expected_learning_unit_years_partim.append(learning_unit_year_expected.academic_year.year)
            else:
                list_of_expected_learning_unit_years_full.append(learning_unit_year_expected.academic_year.year)
        list_of_expected_learning_unit_years_partim.append(learning_unit_partim_annual.end_year + 1)
        list_of_expected_learning_unit_years_partim.append(learning_unit_partim_annual.end_year + 2)

        academic_year_of_new_end_date = None

        edit_learning_unit_end_date(learning_unit_partim_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years_full = _get_list_years_learning_unit(learning_unit_year_subtypes.FULL)
        list_of_learning_unit_years_partim = _get_list_years_learning_unit(learning_unit_year_subtypes.PARTIM)

        self.assertEqual(len(list_of_learning_unit_years_full), len(list_of_expected_learning_unit_years_full))
        self.assertEqual(sorted(list_of_learning_unit_years_partim), list_of_expected_learning_unit_years_partim)

    def test_edit_learning_unit_partim_annual_end_date_is_none_with_start_date_lt_now_with_error(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.current_academic_year.year - 1,
            end_year=self.current_academic_year.year + 4,
        )
        learning_unit_partim_annual = self.setup_learning_unit(
            start_year=self.current_academic_year.year - 1,
            end_year=self.current_academic_year.year + 2,
        )
        self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )

        academic_year_of_new_end_date = None

        with self.assertRaises(IntegrityError):
            edit_learning_unit_end_date(learning_unit_partim_annual, academic_year_of_new_end_date)

    def test_edit_learning_unit_full_annual_end_date_lt_old_end_date_with_start_date_lt_now(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.current_academic_year.year - 1,
            end_year=self.current_academic_year.year + 6,
        )

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual
        )

        list_of_expected_learning_unit_years = []
        for learning_unit_year in list(LearningUnitYear.objects.all()):
            list_of_expected_learning_unit_years.append(learning_unit_year.academic_year.year)
        list_of_expected_learning_unit_years = sorted(list_of_expected_learning_unit_years)
        list_of_expected_learning_unit_years.pop()

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(
            learning_unit_full_annual.end_year - 1
        )

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit()
        self.assertEqual(sorted(list_of_learning_unit_years), list_of_expected_learning_unit_years)

    def test_edit_learning_unit_full_odd_end_date_lt_old_end_date_with_start_date_lt_now(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.current_academic_year.year - 1,
            end_year=self.current_academic_year.year + 6,
            periodicity=learning_unit_periodicity.BIENNIAL_ODD
        )
        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual
        )

        list_of_expected_learning_unit_years = []
        for learning_unit_year in list(LearningUnitYear.objects.all()):
            list_of_expected_learning_unit_years.append(learning_unit_year.academic_year.year)
        list_of_expected_learning_unit_years = sorted(list_of_expected_learning_unit_years)
        year_to_remove = list_of_expected_learning_unit_years.pop()

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(
            year_to_remove - 1
        )

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit()
        self.assertEqual(sorted(list_of_learning_unit_years), list_of_expected_learning_unit_years)

    def test_edit_learning_unit_full_even_end_date_lt_old_end_date_with_start_date_lt_now(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.current_academic_year.year - 1,
            end_year=self.current_academic_year.year + 6,
            periodicity=learning_unit_periodicity.BIENNIAL_EVEN
        )

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual
        )

        list_of_expected_learning_unit_years = []
        for learning_unit_year in list(LearningUnitYear.objects.all()):
            list_of_expected_learning_unit_years.append(learning_unit_year.academic_year.year)
        list_of_expected_learning_unit_years = sorted(list_of_expected_learning_unit_years)
        year_to_remove = list_of_expected_learning_unit_years.pop()

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(
            year_to_remove - 1
        )

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit()
        self.assertEqual(sorted(list_of_learning_unit_years), list_of_expected_learning_unit_years)

    def test_edit_learning_unit_partim_annual_end_date_lt_old_end_date_with_start_date_lt_now(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.current_academic_year.year - 1,
            end_year=self.current_academic_year.year + 6,
        )
        learning_unit_partim_annual = self.setup_learning_unit(
            start_year=self.current_academic_year.year - 1,
            end_year=self.current_academic_year.year + 6,
        )

        list_of_learning_unit_years_annual = self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )

        list_of_expected_learning_unit_years_full = []
        list_of_expected_learning_unit_years_partim = []
        for learning_unit_year_expected in list_of_learning_unit_years_annual:
            if learning_unit_year_expected.subtype == learning_unit_year_subtypes.PARTIM:
                list_of_expected_learning_unit_years_partim.append(learning_unit_year_expected.academic_year.year)
            else:
                list_of_expected_learning_unit_years_full.append(learning_unit_year_expected.academic_year.year)

        list_of_expected_learning_unit_years_partim = sorted(list_of_expected_learning_unit_years_partim)
        year_to_remove = list_of_expected_learning_unit_years_partim.pop()

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(
            year_to_remove - 1
        )

        edit_learning_unit_end_date(learning_unit_partim_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years_full = _get_list_years_learning_unit(learning_unit_year_subtypes.FULL)
        list_of_learning_unit_years_partim = _get_list_years_learning_unit(learning_unit_year_subtypes.PARTIM)

        self.assertEqual(len(list_of_learning_unit_years_full), len(list_of_expected_learning_unit_years_full))
        self.assertEqual(sorted(list_of_learning_unit_years_partim), list_of_expected_learning_unit_years_partim)

    def test_edit_learning_unit_full_annual_end_date_with_wrong_partim_end_year(self):
        start_year = self.current_academic_year.year - 1
        end_year = self.current_academic_year.year + 6

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year, end_year=end_year)
        learning_unit_partim_annual = self.setup_learning_unit(start_year=start_year, end_year=end_year)

        list_partims = self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )
        learning_unit_full_annual.learning_container = list_partims[0].learning_container_year.learning_container
        learning_unit_full_annual.save()
        learning_unit_partim_annual.learning_container = list_partims[0].learning_container_year.learning_container
        learning_unit_partim_annual.save()

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(end_year-3)

        with self.assertRaises(IntegrityError) as context:
            edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        self.assertEqual(str(context.exception),
                         _('partim_greater_than_parent') % {
                    'learning_unit': learning_unit_full_annual.acronym,
                    'partim': list_partims[-1].acronym,
                    'year': academic_year_of_new_end_date}
                         )

    def test_edit_learning_unit_full_annual_end_date_with_wrong_partim_end_year_and_no_luy(self):
        start_year = self.current_academic_year.year - 1
        end_year = self.current_academic_year.year + 6

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year, end_year=end_year)
        learning_unit_partim_annual = self.setup_learning_unit(start_year=start_year, end_year=end_year)

        list_partims = self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now[:2],
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )
        learning_unit_full_annual.learning_container = list_partims[0].learning_container_year.learning_container
        learning_unit_full_annual.save()
        learning_unit_partim_annual.learning_container = list_partims[0].learning_container_year.learning_container
        learning_unit_partim_annual.save()

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(end_year-3)

        with self.assertRaises(IntegrityError) as context:
            edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        self.assertEqual(str(context.exception),
                         _('partim_greater_than_parent') % {
                    'learning_unit': learning_unit_full_annual.acronym,
                    'partim': list_partims[-1].acronym,
                    'year': academic_year_of_new_end_date}
                         )

    def test_edition_learning_extend_with_related_tables(self):
        start_year_full = self.current_academic_year.year
        end_year_full = start_year_full + 6

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)
        learning_unit_years = self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
        )

        _create_learning_component_years(learning_unit_years, self.number_classes)
        _create_entity_container_years(learning_unit_years, self.entity)

        excepted_end_year = end_year_full + 2
        self._edit_lu(learning_unit_full_annual, excepted_end_year)

        last_luy = LearningUnitYear.objects.filter(learning_unit=learning_unit_full_annual
                                                   ).order_by('academic_year').last()
        last_container = last_luy.learning_container_year

        # check if the link with entity is correctly duplicated
        last_ecy = EntityContainerYear.objects.filter(learning_container_year=last_container).last()
        self.assertEqual(last_ecy.entity, self.entity)
        last_e_component_year = EntityComponentYear.objects.filter(entity_container_year=last_ecy).last()
        self.assertEqual(last_e_component_year.entity_container_year.entity, self.entity)

        # check if the classes are correctly duplicated
        component = LearningComponentYear.objects.filter(learning_container_year=last_container).last()
        self.assertEqual(LearningClassYear.objects.filter(learning_component_year=component).count(),
                         self.number_classes)

        # check if the learning unit component is correctly duplicated
        self.assertTrue(LearningUnitComponent.objects.filter(learning_component_year=component,
                                                             learning_unit_year=last_luy).exists())

    def test_shorten_and_extend_learning_unit(self):
        start_year_full = self.current_academic_year.year
        end_year_full = start_year_full + 6

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)
        learning_unit_years = self.setup_list_of_learning_unit_years_full(self.list_of_academic_years_after_now,
                                                                          learning_unit_full_annual)

        _create_learning_component_years(learning_unit_years, self.number_classes)
        _create_entity_container_years(learning_unit_years, self.entity)

        # shorten & extend lu
        excepted_end_year = end_year_full - 2
        self._edit_lu(learning_unit_full_annual, excepted_end_year)

        excepted_end_year += 2
        self._edit_lu(learning_unit_full_annual, excepted_end_year)

        excepted_end_year -= 2
        self._edit_lu(learning_unit_full_annual, excepted_end_year)

        excepted_end_year += 3
        self._edit_lu(learning_unit_full_annual, excepted_end_year)

        excepted_end_year -= 4
        self._edit_lu(learning_unit_full_annual, excepted_end_year)

    def test_extend_learning_unit_with_wrong_entity(self):
        start_year_full = self.current_academic_year.year
        end_year_full = start_year_full + 6

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)
        learning_unit_years = self.setup_list_of_learning_unit_years_full(self.list_of_academic_years_after_now,
                                                                          learning_unit_full_annual)

        _create_learning_component_years(learning_unit_years, self.number_classes)
        _create_entity_container_years(learning_unit_years, self.entity)

        self.entity_version.end_date = self.current_academic_year.end_date
        self.entity_version.save()
        excepted_end_year = end_year_full + 3
        with self.assertRaises(IntegrityError) as e:
            self._edit_lu(learning_unit_full_annual, excepted_end_year)

        self.assertEqual(str(e.exception), _('Entity_not_exist') % {
            'entity_acronym': self.entity_version.acronym,
            'academic_year': academic_year.find_academic_year_by_year(end_year_full+1)
        })

    def test_with_partim_fields_that_are_not_reported(self):
        lu_full = self.setup_learning_unit(start_year=self.current_academic_year.year,
                                           end_year=self.list_of_academic_years_after_now[3].year)
        lu_partim =  self.setup_learning_unit(start_year=self.current_academic_year.year,
                                              end_year=self.current_academic_year.year)
        lu_year_partims = self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now[:4],
            learning_unit_full=lu_full,
            learning_unit_partim=lu_partim
        )

        for partim in lu_year_partims[2:]:
            partim.delete()

        lu_year_partims[1].attribution_procedure = attribution_procedure.INTERNAL_TEAM
        lu_year_partims[1].save()
        lu_year_partims[1].learning_container_year.is_vacant = True
        lu_year_partims[1].learning_container_year.team = True
        lu_year_partims[1].learning_container_year.save()


        edit_learning_unit_end_date(lu_partim, self.list_of_academic_years_after_now[3])
        created_partims = list(
            LearningUnitYear.objects.filter(subtype=learning_unit_year_subtypes.PARTIM)
                .exclude(id=lu_year_partims[1].id)
        )

        self.assertEqual(len(created_partims), 3)

        for partim in created_partims:
            self.assertIsNone(partim.attribution_procedure)
            self.assertFalse(partim.learning_container_year.is_vacant)
            self.assertTrue(partim.learning_container_year.team)

    def _edit_lu(self, learning_unit_full_annual, excepted_end_year):
        excepted_nb_msg = abs(learning_unit_full_annual.end_year - excepted_end_year) + 1
        list_of_expected_years = list(range(learning_unit_full_annual.start_year, excepted_end_year+1))

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(excepted_end_year)
        result = edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        self.assertEqual(len(result), excepted_nb_msg)
        list_of_years_learning_unit = _get_list_years_learning_unit(learning_unit_year_subtypes.FULL)
        self.assertEqual(list_of_years_learning_unit, list_of_expected_years)
        self.assertEqual(learning_unit_full_annual.end_year, excepted_end_year)


def _create_classes(learning_component_year, number_classes):
    for i in range(number_classes):
        LearningClassYearFactory(learning_component_year=learning_component_year)


def _create_entity_container_years(learning_unit_years, entity=None):
    if not entity:
        entity = EntityFactory()

    for lu in learning_unit_years:
        entity_container_year = EntityContainerYearFactory(learning_container_year=lu.learning_container_year,
                                                           entity=entity)
        EntityComponentYearFactory(entity_container_year=entity_container_year)


def _create_learning_component_years(learning_unit_years, number_classes=None):
    for luy in learning_unit_years:
        luc = LearningUnitComponentFactory(learning_unit_year=luy)
        component = luc.learning_component_year
        component.learning_container_year = luy.learning_container_year
        component.save()
        if number_classes:
            _create_classes(component, number_classes)


def _get_list_years_learning_unit(subtype=learning_unit_year_subtypes.FULL):
    return list(
        LearningUnitYear.objects.filter(
            subtype=subtype).values_list('academic_year__year', flat=True).order_by('academic_year')
    )

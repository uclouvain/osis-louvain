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
from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.forms import model_to_dict
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from base.business.learning_units.edition import edit_learning_unit_end_date, update_learning_unit_year_with_report, \
    ConsistencyError
from base.models import academic_year
from base.models import learning_unit_year as mdl_luy
from base.models import teaching_material as mdl_teaching_material
from base.models.academic_year import compute_max_academic_year_adjournment
from base.models.entity_container_year import EntityContainerYear
from base.models.enums import learning_component_year_type
from base.models.enums import learning_unit_year_subtypes, learning_unit_year_periodicity, \
    learning_container_year_types, attribution_procedure, internship_subtypes, learning_unit_year_session, \
    quadrimesters, vacant_declaration_type, entity_container_year_link_type
from base.models.learning_class_year import LearningClassYear
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.business.learning_units import LearningUnitsMixin, GenerateContainer
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from cms.models import translated_text
from reference.tests.factories.language import LanguageFactory


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
            academic_year=self.starting_academic_year,
            container_type=learning_container_year_types.COURSE
        )
        self.number_classes = 5
        self.entity_version = EntityVersionFactory(start_date=datetime.now(), end_date=datetime(3000, 1, 1))
        self.entity = self.entity_version.entity

    def test_edit_learning_unit_full_annual_end_date_gt_old_end_date_with_start_date_gt_now(self):
        start_year = self.starting_academic_year.year + 1
        end_year = self.starting_academic_year.year + 3
        expected_end_year = end_year + 2
        list_of_expected_learning_unit_years = list(range(start_year, expected_end_year + 1))

        learning_unit_full_annual = self.setup_learning_unit(
            start_year=start_year,
            end_year=end_year,
        )

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(expected_end_year)

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit(learning_unit_full_annual)
        self.assertEqual(list_of_learning_unit_years, list_of_expected_learning_unit_years)

    def test_edit_learning_unit_partim_annual_end_date_gt_old_end_date_with_start_date_gt_now(self):
        start_year_full = self.starting_academic_year.year + 1
        end_year_full = self.starting_academic_year.year + 6

        start_year_partim = self.starting_academic_year.year + 2
        end_year_partim = self.starting_academic_year.year + 3
        excepted_end_year_partim = end_year_partim + 2

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)
        learning_unit_partim_annual = self.setup_learning_unit(start_year=start_year_partim, end_year=end_year_partim)

        self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )

        list_of_expected_learning_unit_years_full = list(range(start_year_full, end_year_full + 1))
        list_of_expected_learning_unit_years_partim = list(range(start_year_partim, excepted_end_year_partim + 1))

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(excepted_end_year_partim)

        edit_learning_unit_end_date(learning_unit_partim_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years_full = _get_list_years_learning_unit(learning_unit_full_annual)
        list_of_learning_unit_years_partim = _get_list_years_learning_unit(learning_unit_partim_annual)

        self.assertEqual(len(list_of_learning_unit_years_full), len(list_of_expected_learning_unit_years_full))
        self.assertEqual(list_of_learning_unit_years_partim, list_of_expected_learning_unit_years_partim)

    def test_edit_learning_unit_full_annual_end_date_gt_old_end_date_with_start_date_lt_now(self):
        start_year_full = self.starting_academic_year.year - 1
        end_year_full = self.starting_academic_year.year + 1
        expected_end_year_full = end_year_full + 2

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )

        list_of_expected_learning_unit_years = list(range(start_year_full, expected_end_year_full + 1))
        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(expected_end_year_full)

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit(learning_unit_full_annual)
        self.assertEqual(list_of_learning_unit_years, list_of_expected_learning_unit_years)

    def test_edit_learning_unit_partim_annual_end_gt_old_end_date_date_with_start_date_lt_now(self):
        start_year_full = self.starting_academic_year.year - 1
        end_year_full = self.starting_academic_year.year + 3

        start_year_partim = self.starting_academic_year.year - 1
        end_year_partim = self.starting_academic_year.year + 1
        excepted_end_year_partim = end_year_partim + 2

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
            if learning_unit_year_expected.is_partim():
                list_of_expected_learning_unit_years_partim.append(learning_unit_year_expected.academic_year.year)
            else:
                list_of_expected_learning_unit_years_full.append(learning_unit_year_expected.academic_year.year)
        list_of_expected_learning_unit_years_partim.append(learning_unit_partim_annual.end_year + 1)
        list_of_expected_learning_unit_years_partim.append(learning_unit_partim_annual.end_year + 2)

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(excepted_end_year_partim)

        edit_learning_unit_end_date(learning_unit_partim_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years_full = _get_list_years_learning_unit(learning_unit_full_annual)
        list_of_learning_unit_years_partim = _get_list_years_learning_unit(learning_unit_partim_annual)

        self.assertEqual(list_of_learning_unit_years_full, list_of_expected_learning_unit_years_full)
        self.assertEqual(list_of_learning_unit_years_partim, list_of_expected_learning_unit_years_partim)

    def test_edit_learning_unit_full_annual_end_date_is_none_with_start_date_lt_now(self):
        start_year = self.starting_academic_year.year - 1
        end_year = self.starting_academic_year.year + 4
        expected_end_year = end_year + 2
        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year, end_year=end_year)

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )

        list_of_expected_learning_unit_years = list(range(start_year, expected_end_year + 1))
        academic_year_of_new_end_date = None

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years = _get_list_years_learning_unit(learning_unit_full_annual)
        self.assertEqual(list_of_learning_unit_years, list_of_expected_learning_unit_years)

    def test_edit_learning_unit_partim_annual_end_date_is_none_with_start_date_lt_now(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.starting_academic_year.year - 1,
            end_year=self.starting_academic_year.year + 6,
        )
        learning_unit_partim_annual = self.setup_learning_unit(
            start_year=self.starting_academic_year.year - 1,
            end_year=self.starting_academic_year.year + 4,
        )

        self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )

        with self.assertRaises(IntegrityError):
            edit_learning_unit_end_date(learning_unit_partim_annual, None)

    def test_edit_learning_unit_partim_annual_end_date_is_none_with_start_date_lt_now_with_error(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.starting_academic_year.year - 1,
            end_year=self.starting_academic_year.year + 4,
        )
        learning_unit_partim_annual = self.setup_learning_unit(
            start_year=self.starting_academic_year.year - 1,
            end_year=self.starting_academic_year.year + 2,
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
            start_year=self.starting_academic_year.year - 1,
            end_year=self.starting_academic_year.year + 6,
        )

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.ANNUAL
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

        list_of_learning_unit_years = _get_list_years_learning_unit(learning_unit_full_annual)
        self.assertEqual(sorted(list_of_learning_unit_years), list_of_expected_learning_unit_years)

    def test_edit_learning_unit_full_odd_end_date_lt_old_end_date_with_start_date_lt_now(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.starting_academic_year.year - 1,
            end_year=self.starting_academic_year.year + 6
        )
        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.BIENNIAL_ODD
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

        list_of_learning_unit_years = _get_list_years_learning_unit(learning_unit_full_annual)
        self.assertEqual(sorted(list_of_learning_unit_years), list_of_expected_learning_unit_years)

    def test_edit_learning_unit_full_even_end_date_lt_old_end_date_with_start_date_lt_now(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.starting_academic_year.year - 1,
            end_year=self.starting_academic_year.year + 6
        )

        self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.BIENNIAL_EVEN
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

        list_of_learning_unit_years = _get_list_years_learning_unit(learning_unit_full_annual)
        self.assertEqual(sorted(list_of_learning_unit_years), list_of_expected_learning_unit_years)

    def test_edit_learning_unit_partim_annual_end_date_lt_old_end_date_with_start_date_lt_now(self):
        learning_unit_full_annual = self.setup_learning_unit(
            start_year=self.starting_academic_year.year - 1,
            end_year=self.starting_academic_year.year + 6,
        )
        learning_unit_partim_annual = self.setup_learning_unit(
            start_year=self.starting_academic_year.year - 1,
            end_year=self.starting_academic_year.year + 6,
        )

        list_of_learning_unit_years_annual = self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )

        list_of_expected_learning_unit_years_full = []
        list_of_expected_learning_unit_years_partim = []
        for learning_unit_year_expected in list_of_learning_unit_years_annual:
            if learning_unit_year_expected.is_partim():
                list_of_expected_learning_unit_years_partim.append(learning_unit_year_expected.academic_year.year)
            else:
                list_of_expected_learning_unit_years_full.append(learning_unit_year_expected.academic_year.year)

        list_of_expected_learning_unit_years_partim = sorted(list_of_expected_learning_unit_years_partim)
        year_to_remove = list_of_expected_learning_unit_years_partim.pop()

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(
            year_to_remove - 1
        )

        edit_learning_unit_end_date(learning_unit_partim_annual, academic_year_of_new_end_date)

        list_of_learning_unit_years_full = _get_list_years_learning_unit(learning_unit_full_annual)
        list_of_learning_unit_years_partim = _get_list_years_learning_unit(learning_unit_partim_annual)

        self.assertEqual(len(list_of_learning_unit_years_full), len(list_of_expected_learning_unit_years_full))
        self.assertEqual(sorted(list_of_learning_unit_years_partim), list_of_expected_learning_unit_years_partim)

    def test_edit_learning_unit_full_annual_end_date_with_wrong_partim_end_year(self):
        start_year = self.starting_academic_year.year - 1
        end_year = self.starting_academic_year.year + 6

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

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(end_year - 3)

        with self.assertRaises(IntegrityError) as context:
            edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        self.assertEqual(str(context.exception),
                         _('The learning unit %(learning_unit)s has a partim %(partim)s with'
                           ' an end year greater than %(year)s') % {
                             'learning_unit': learning_unit_full_annual.acronym,
                             'partim': list_partims[1].acronym,
                             'year': academic_year_of_new_end_date}
                         )

    def test_edit_learning_unit_full_annual_end_date_with_wrong_partim_end_year_and_no_luy(self):
        start_year = self.starting_academic_year.year - 1
        end_year = self.starting_academic_year.year + 6

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

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(end_year - 3)

        with self.assertRaises(IntegrityError) as context:
            edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        self.assertEqual(str(context.exception),
                         _('The learning unit %(learning_unit)s has a partim %(partim)s with'
                           ' an end year greater than %(year)s') % {
                             'learning_unit': learning_unit_full_annual.acronym,
                             'partim': list_partims[1].acronym,
                             'year': academic_year_of_new_end_date}
                         )

    def test_edit_learning_unit_full_end_year_max_value_with_partim_end_year_none(self):
        start_year = self.starting_academic_year.year - 1
        max_end_year = compute_max_academic_year_adjournment()

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year, end_year=None)
        learning_unit_partim_annual = self.setup_learning_unit(start_year=start_year, end_year=None)

        list_partims = self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now[:2],
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )
        learning_unit_full_annual.learning_container = list_partims[0].learning_container_year.learning_container
        learning_unit_full_annual.save()
        learning_unit_partim_annual.learning_container = list_partims[0].learning_container_year.learning_container
        learning_unit_partim_annual.save()

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(max_end_year)

        with self.assertRaises(IntegrityError) as context:
            edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        self.assertEqual(str(context.exception),
                         _('The learning unit %(learning_unit)s has a partim %(partim)s '
                           'with an end year greater than %(year)s') % {
                             'learning_unit': learning_unit_full_annual.acronym,
                             'partim': list_partims[1].acronym,
                             'year': academic_year_of_new_end_date}
                         )

    def test_edit_learning_unit_full_end_year_max_value_with_partim_end_year(self):
        start_year = self.starting_academic_year.year
        max_end_year = compute_max_academic_year_adjournment()

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year, end_year=None)
        learning_unit_partim_annual = self.setup_learning_unit(start_year=start_year, end_year=None)

        list_partims = self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )
        learning_unit_full_annual.learning_container = list_partims[0].learning_container_year.learning_container
        learning_unit_full_annual.save()
        learning_unit_partim_annual.learning_container = list_partims[0].learning_container_year.learning_container
        learning_unit_partim_annual.save()

        self._edit_lu(learning_unit_partim_annual, max_end_year)
        self._edit_lu(learning_unit_full_annual, max_end_year)

    def test_edit_learning_unit_full_end_year_none_value_with_partim_end_year(self):
        start_year = self.starting_academic_year.year
        max_end_year = compute_max_academic_year_adjournment()

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year, end_year=max_end_year)
        learning_unit_partim_annual = self.setup_learning_unit(start_year=start_year, end_year=max_end_year)

        list_partims = self.setup_list_of_learning_unit_years_partim(
            list_of_academic_years=self.list_of_academic_years_after_now,
            learning_unit_full=learning_unit_full_annual,
            learning_unit_partim=learning_unit_partim_annual
        )
        learning_unit_full_annual.learning_container = list_partims[0].learning_container_year.learning_container
        learning_unit_full_annual.save()
        learning_unit_partim_annual.learning_container = list_partims[0].learning_container_year.learning_container
        learning_unit_partim_annual.save()

        with self.assertRaises(IntegrityError) as context:
            edit_learning_unit_end_date(learning_unit_partim_annual, None)

        self.assertEqual(str(context.exception),
                         _('The selected end year (%(partim_end_year)s) is greater '
                           'than the end year of the parent %(lu_parent)s') % {
                             'partim_end_year': academic_year.find_academic_year_by_year(max_end_year + 1),
                             'lu_parent': learning_unit_full_annual.acronym
                         })

    def test_shorten_and_extend_learning_unit_partim_end_year_to_none(self):
        start_year_full = self.starting_academic_year.year

        generator_learning_container = GenerateContainer(start_year=start_year_full,
                                                         end_year=compute_max_academic_year_adjournment())

        generator_learning_container.learning_unit_partim.end_year = None
        generator_learning_container.learning_unit_partim.save()

        excepted_end_year = start_year_full + 2
        self._edit_lu(generator_learning_container.learning_unit_partim, excepted_end_year)

        excepted_end_year += 2
        self._edit_lu(generator_learning_container.learning_unit_partim, excepted_end_year)

        with self.assertRaises(IntegrityError):
            self._edit_lu(generator_learning_container.learning_unit_partim, None)

    def test_edition_learning_extend_with_related_tables(self):
        start_year_full = self.starting_academic_year.year
        end_year_full = start_year_full + 6

        generator_learning_container = GenerateContainer(start_year=start_year_full, end_year=end_year_full)

        excepted_end_year = end_year_full + 2
        self._edit_lu(generator_learning_container.learning_unit_full, excepted_end_year)

        last_generated_luy = LearningUnitYear.objects.filter(
            learning_unit=generator_learning_container.learning_unit_full
        ).order_by('academic_year').last()

        last_container = last_generated_luy.learning_container_year

        self._assert_entity_container_year_correctly_duplicated(generator_learning_container.entities, last_container)
        expected_entities = [
            entity_container_year.entity
            for entity_container_year in
            generator_learning_container.generated_container_years[0].list_repartition_volume_entities
        ]

        last_generated_component = LearningComponentYear.objects.filter(learning_unit_year=last_generated_luy).last()
        self.assertEqual(last_generated_luy.learning_container_year, last_generated_component.learning_unit_year.learning_container_year)

        self._assert_learning_classes_correctly_duplicated(
            last_generated_component,
            generator_learning_container.generated_container_years[0].nb_classes
        )

    def _assert_learning_classes_correctly_duplicated(self, component, expected_nb_classes):
        self.assertEqual(LearningClassYear.objects.filter(learning_component_year=component).count(),
                         expected_nb_classes)

    def _assert_entity_container_year_correctly_duplicated(self, expected_entities, duplicated_container):
        qs_entity_container_year = EntityContainerYear.objects.filter(learning_container_year=duplicated_container)
        self.assertEqual(qs_entity_container_year.count(), 4)
        for entity_container_year in qs_entity_container_year:
            self.assertIn(entity_container_year.entity, expected_entities)

    def test_shorten_and_extend_learning_unit(self):
        start_year_full = self.starting_academic_year.year
        end_year_full = start_year_full + 6

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)
        learning_unit_years = self.setup_list_of_learning_unit_years_full(
            self.list_of_academic_years_after_now,
            learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )

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
        start_year_full = self.starting_academic_year.year
        end_year_full = start_year_full + 6

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)
        learning_unit_years = self.setup_list_of_learning_unit_years_full(
            self.list_of_academic_years_after_now,
            learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )

        _create_learning_component_years(learning_unit_years, self.number_classes)
        _create_entity_container_years(learning_unit_years, self.entity)

        self.entity_version.end_date = self.starting_academic_year.end_date
        self.entity_version.save()
        excepted_end_year = end_year_full + 3
        with self.assertRaises(IntegrityError) as e:
            self._edit_lu(learning_unit_full_annual, excepted_end_year)

        self.assertEqual(str(e.exception), _('The entity %(entity_acronym)s does not exist for '
                                             'the selected academic year %(academic_year)s') % {
            'entity_acronym': self.entity_version.acronym,
            'academic_year': academic_year.find_academic_year_by_year(end_year_full + 1)
        })

    def test_with_partim_fields_that_are_not_reported(self):
        lu_full = self.setup_learning_unit(start_year=self.starting_academic_year.year,
                                           end_year=self.list_of_academic_years_after_now[3].year)
        lu_partim = self.setup_learning_unit(start_year=self.starting_academic_year.year,
                                             end_year=self.starting_academic_year.year)
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
            LearningUnitYear.objects.filter(
                subtype=learning_unit_year_subtypes.PARTIM
            ).exclude(id=lu_year_partims[1].id)
        )

        self.assertEqual(len(created_partims), 3)

        for partim in created_partims:
            self.assertIsNone(partim.attribution_procedure)
            self.assertFalse(partim.learning_container_year.is_vacant)
            self.assertTrue(partim.learning_container_year.team)

    def _edit_lu(self, learning_unit_annual, excepted_end_year):
        end_year = learning_unit_annual.end_year or compute_max_academic_year_adjournment()
        if not excepted_end_year:
            new_end_year = compute_max_academic_year_adjournment()
        else:
            new_end_year = excepted_end_year

        excepted_nb_msg = abs(end_year - new_end_year) + 1
        list_of_expected_years = list(range(learning_unit_annual.start_year, new_end_year + 1))

        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(excepted_end_year)
        result = edit_learning_unit_end_date(learning_unit_annual, academic_year_of_new_end_date)

        self.assertTrue(len(result) >= excepted_nb_msg)
        list_of_years_learning_unit = _get_list_years_learning_unit(learning_unit_annual)
        self.assertEqual(list_of_years_learning_unit, list_of_expected_years)
        self.assertEqual(learning_unit_annual.end_year, excepted_end_year)

    def test_postpone_end_date_with_cms_data_and_teaching_material(self):
        start_year_full = self.starting_academic_year.year - 1
        end_year_full = self.starting_academic_year.year + 1
        expected_end_year_full = end_year_full + 2
        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(expected_end_year_full)

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)

        luy_list = self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )

        self.setup_educational_information(luy_list)

        last_luy = mdl_luy.find_latest_by_learning_unit(learning_unit_full_annual)
        last_luy_teaching_material_count = mdl_teaching_material.find_by_learning_unit_year(last_luy).count()
        last_luy_educational_information = translated_text.build_list_of_cms_content_by_reference(last_luy.id)

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        new_luy = mdl_luy.find_latest_by_learning_unit(learning_unit_full_annual)
        new_luy_teaching_material_count = mdl_teaching_material.find_by_learning_unit_year(new_luy).count()
        new_luy_educational_information = translated_text.build_list_of_cms_content_by_reference(new_luy.id)

        self.assertEqual(last_luy_teaching_material_count, new_luy_teaching_material_count)
        self.assertCountEqual(last_luy_educational_information, new_luy_educational_information)

    def test_postpone_end_date_with_external_learning_unit(self):
        start_year_full = self.starting_academic_year.year - 1
        end_year_full = self.starting_academic_year.year + 1
        expected_end_year_full = end_year_full + 2
        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(expected_end_year_full)

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)

        luy_list = self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )
        for luy in luy_list:
            ExternalLearningUnitYearFactory(learning_unit_year=luy, external_acronym="Yolo")

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        new_luy = mdl_luy.find_latest_by_learning_unit(learning_unit_full_annual)

        self.assertEqual(new_luy.externallearningunityear.external_acronym, "Yolo")

    def test_shorten_end_date_with_external_learning_unit(self):
        start_year_full = self.starting_academic_year.year - 3
        end_year_full = self.starting_academic_year.year
        expected_end_year_full = end_year_full - 2
        academic_year_of_new_end_date = academic_year.find_academic_year_by_year(expected_end_year_full)

        learning_unit_full_annual = self.setup_learning_unit(start_year=start_year_full, end_year=end_year_full)

        luy_list = self.setup_list_of_learning_unit_years_full(
            list_of_academic_years=self.list_of_academic_years,
            learning_unit_full=learning_unit_full_annual,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )
        for luy in luy_list:
            ExternalLearningUnitYearFactory(learning_unit_year=luy, external_acronym="Yolo")

        edit_learning_unit_end_date(learning_unit_full_annual, academic_year_of_new_end_date)

        new_luy = mdl_luy.find_latest_by_learning_unit(learning_unit_full_annual)
        self.assertEqual(learning_unit_full_annual.end_year, academic_year_of_new_end_date.year)
        self.assertEqual(new_luy.externallearningunityear.external_acronym, "Yolo")


def _create_classes(learning_component_year, number_classes):
    for i in range(number_classes):
        LearningClassYearFactory(learning_component_year=learning_component_year)


def _create_entity_container_years(learning_unit_years, entity=None):
    if not entity:
        entity = EntityFactory()

    for lu in learning_unit_years:
        entity_container_year = EntityContainerYearFactory(learning_container_year=lu.learning_container_year,
                                                           entity=entity)


def _create_learning_component_years(learning_unit_years, number_classes=None):
    for luy in learning_unit_years:
        component = LearningComponentYearFactory(learning_unit_year=luy)
        if number_classes:
            _create_classes(component, number_classes)


def _get_list_years_learning_unit(learning_unit):
    return list(
        LearningUnitYear.objects.filter(learning_unit=learning_unit
                                        ).values_list('academic_year__year', flat=True).order_by('academic_year')
    )


class TestModifyLearningUnit(TestCase, LearningUnitsMixin):
    def setUp(self):
        super().setUp()
        self.setup_academic_years()
        self.learning_container_year = LearningContainerYearFactory(academic_year=self.starting_academic_year)
        self.learning_unit_year = LearningUnitYearFactory(learning_container_year=self.learning_container_year,
                                                          subtype=learning_unit_year_subtypes.FULL)
        self.other_language = LanguageFactory()
        self.other_campus = CampusFactory()

    def test_with_no_fields_to_update(self):
        old_luy_values = model_to_dict(self.learning_unit_year, exclude="learning_component_years")
        old_lc_values = model_to_dict(self.learning_container_year)

        update_learning_unit_year_with_report(self.learning_unit_year, {}, {})

        self.learning_unit_year.refresh_from_db()
        self.learning_container_year.refresh_from_db()
        new_luy_values = model_to_dict(self.learning_unit_year, exclude="learning_component_years")
        new_lc_values = model_to_dict(self.learning_container_year)

        self.maxDiff = None
        self.assertDictEqual(old_luy_values, new_luy_values)
        self.assertDictEqual(old_lc_values, new_lc_values)

    def test_with_learning_unit_fields_to_update(self):
        fields_to_update = {
            "faculty_remark": "Faculty remark",
            "other_remark": "Other remark"
        }
        update_learning_unit_year_with_report(self.learning_unit_year, fields_to_update, {})

        self.assert_fields_updated(self.learning_unit_year.learning_unit, fields_to_update)

    def test_with_learning_unit_year_fields_to_update(self):
        fields_to_update = {
            "specific_title": "Mon cours",
            "specific_title_english": "My course",
            "credits": Decimal('45.00'),
            "internship_subtype": internship_subtypes.PROFESSIONAL_INTERNSHIP,
            "status": False,
            "session": learning_unit_year_session.SESSION_123,
            "quadrimester": quadrimesters.Q2,
            "attribution_procedure": attribution_procedure.EXTERNAL,
            "language": self.other_language
        }

        update_learning_unit_year_with_report(self.learning_unit_year, fields_to_update, {})
        fields_to_update["language"] = fields_to_update["language"].pk
        self.assert_fields_updated(self.learning_unit_year, fields_to_update)

    def test_with_learning_container_year_fields_to_update(self):
        fields_to_update = {
            "common_title": "Mon common",
            "common_title_english": "My common",
            "team": True,
            "is_vacant": True,
            "type_declaration_vacant": vacant_declaration_type.VACANT_NOT_PUBLISH
        }

        update_learning_unit_year_with_report(self.learning_unit_year, fields_to_update, {})
        self.learning_container_year.refresh_from_db()

        new_lcy_values = model_to_dict(self.learning_container_year, fields=fields_to_update.keys())
        expected_model_dict_values = fields_to_update

        self.assertDictEqual(expected_model_dict_values, new_lcy_values)

    def test_apply_updates_on_next_learning_unit_years(self):
        a_learning_unit = self.setup_learning_unit(self.starting_academic_year.year)
        learning_unit_years = self.setup_list_of_learning_unit_years_full(self.list_of_academic_years_after_now,
                                                                          a_learning_unit,
                                                                          learning_unit_year_periodicity.ANNUAL)

        learning_unit_fields_to_update = {
            "faculty_remark": "Faculty remark"
        }
        learning_unit_year_fields_to_update = {
            "specific_title_english": "My course",
            "credits": 45,
            "attribution_procedure": attribution_procedure.EXTERNAL
        }
        learning_container_year_fields_to_update = {
            "team": True,
            "is_vacant": True,
            "type_declaration_vacant": vacant_declaration_type.VACANT_NOT_PUBLISH
        }

        fields_to_update = dict()
        fields_to_update.update(learning_unit_fields_to_update)
        fields_to_update.update(learning_unit_year_fields_to_update)
        fields_to_update.update(learning_container_year_fields_to_update)
        update_learning_unit_year_with_report(learning_unit_years[1], fields_to_update, {},
                                              override_postponement_consistency=True)

        self.assert_fields_not_updated(learning_unit_years[0], exclude="learning_component_years")
        self.assert_fields_not_updated(learning_unit_years[0].learning_container_year)

        for index, luy in enumerate(learning_unit_years[1:]):
            self.assert_fields_updated(luy.learning_unit, learning_unit_fields_to_update)
            if index == 0:
                self.assert_fields_updated(luy, learning_unit_year_fields_to_update)
                self.assert_fields_updated(luy.learning_container_year, learning_container_year_fields_to_update)
            else:
                self.assert_fields_updated(luy.learning_container_year, learning_container_year_fields_to_update,
                                           exclude=["is_vacant", "type_declaration_vacant", 'team'])
                self.assert_fields_not_updated(luy.learning_container_year, fields=["team"])
                self.assert_fields_updated(luy, learning_unit_year_fields_to_update, exclude=["attribution_procedure"])
                self.assert_fields_not_updated(luy, fields=["attribution_procedure"])

    def test_apply_updates_on_next_learning_unit_years_until_proposal(self):
        a_learning_unit = self.setup_learning_unit(self.starting_academic_year.year)
        learning_unit_years = self.setup_list_of_learning_unit_years_full(
            self.list_of_academic_years_after_now, a_learning_unit,
            periodicity=learning_unit_year_periodicity.ANNUAL)

        luy_in_proposal = learning_unit_years[2]
        ProposalLearningUnitFactory(learning_unit_year=luy_in_proposal)

        learning_unit_fields_to_update = {
            "faculty_remark": "Faculty remark"
        }
        learning_unit_year_fields_to_update = {
            "specific_title_english": "My course",
            "credits": 45,
            "attribution_procedure": attribution_procedure.EXTERNAL
        }
        learning_container_year_fields_to_update = {
            "team": True,
            "is_vacant": True,
            "type_declaration_vacant": vacant_declaration_type.VACANT_NOT_PUBLISH
        }

        fields_to_update = dict()
        fields_to_update.update(learning_unit_fields_to_update)
        fields_to_update.update(learning_unit_year_fields_to_update)
        fields_to_update.update(learning_container_year_fields_to_update)

        error_msg = _("The learning unit %(luy)s is in proposal, can not"
                      " save the change from the year %(academic_year)s") % {
            'luy': luy_in_proposal.acronym,
            'academic_year': luy_in_proposal.academic_year
        }

        with self.assertRaises(ConsistencyError) as context:
            update_learning_unit_year_with_report(learning_unit_years[1], fields_to_update, {})

        self.assertIn(error_msg, context.exception.error_list)

    def test_when_not_reporting(self):
        a_learning_unit = self.setup_learning_unit(self.starting_academic_year.year)
        learning_unit_years = self.setup_list_of_learning_unit_years_full(
            self.list_of_academic_years_after_now,
            a_learning_unit,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )

        learning_unit_fields_to_update = {
            "faculty_remark": "Faculty remark"
        }
        learning_unit_year_fields_to_update = {
            "specific_title_english": "My course",
            "credits": 45,
            "attribution_procedure": attribution_procedure.EXTERNAL
        }
        learning_container_year_fields_to_update = {
            "team": True,
            "is_vacant": True,
            "type_declaration_vacant": vacant_declaration_type.VACANT_NOT_PUBLISH
        }

        fields_to_update = dict()
        fields_to_update.update(learning_unit_fields_to_update)
        fields_to_update.update(learning_unit_year_fields_to_update)
        fields_to_update.update(learning_container_year_fields_to_update)

        update_learning_unit_year_with_report(learning_unit_years[0], fields_to_update, {}, with_report=False)

        self.assert_fields_updated(learning_unit_years[0].learning_unit, learning_unit_fields_to_update)
        self.assert_fields_updated(learning_unit_years[0], learning_unit_year_fields_to_update)
        self.assert_fields_updated(learning_unit_years[0].learning_container_year,
                                   learning_container_year_fields_to_update)

        for luy in learning_unit_years[1:]:
            self.assert_fields_not_updated(luy, exclude="learning_component_years")
            self.assert_fields_not_updated(luy.learning_container_year)

    def assert_fields_updated(self, instance, fields_value, exclude=None):
        if exclude is None:
            exclude = []
        instance.refresh_from_db()

        instance_values = model_to_dict(instance, fields=fields_value.keys(), exclude=exclude)
        fields_value_without_excluded = {field: value for field, value in fields_value.items() if field not in exclude}
        self.assertDictEqual(fields_value_without_excluded, instance_values)

    def assert_fields_not_updated(self, instance, fields=None, exclude=None):

        past_instance_values = model_to_dict(instance, fields, exclude)

        instance.refresh_from_db()
        new_instance_values = model_to_dict(instance, fields, exclude)
        self.maxDiff = None

        self.assertDictEqual(past_instance_values, new_instance_values)


class TestUpdateLearningUnitEntities(TestCase, LearningUnitsMixin):
    def setUp(self):
        self.setup_academic_years()
        self.learning_container_year = LearningContainerYearFactory(
            academic_year=self.starting_academic_year,
            container_type=learning_container_year_types.COURSE,
            type_declaration_vacant=vacant_declaration_type.DO_NOT_ASSIGN)
        self.learning_unit_year = LearningUnitYearFactory(
            learning_container_year=self.learning_container_year,
            academic_year=self.starting_academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            attribution_procedure=attribution_procedure.INTERNAL_TEAM)
        self.learning_component_year = LearningComponentYearFactory(
            learning_unit_year=self.learning_unit_year,
            acronym="PM",
            type=learning_component_year_type.LECTURING)

        self.requirement_entity_container = EntityContainerYearFactory(
            learning_container_year=self.learning_container_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY)

        self.allocation_entity_container = EntityContainerYearFactory(
            learning_container_year=self.learning_container_year,
            type=entity_container_year_link_type.ALLOCATION_ENTITY)

        self.additional_entity_container_1 = EntityContainerYearFactory(
            learning_container_year=self.learning_container_year,
            type=entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1)

        self.additional_entity_container_2 = EntityContainerYearFactory(
            learning_container_year=self.learning_container_year,
            type=entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2)

    def test_with_no_entities_to_update(self):
        update_learning_unit_year_with_report(self.learning_unit_year, {}, {})

        self.assert_entity_has_not_changed(self.requirement_entity_container)
        self.assert_entity_has_not_changed(self.allocation_entity_container)
        self.assert_entity_has_not_changed(self.additional_entity_container_1)
        self.assert_entity_has_not_changed(self.additional_entity_container_2)

    def test_with_one_entity_to_update(self):
        a_new_requirement_entity = EntityFactory()
        entities_to_update = {entity_container_year_link_type.REQUIREMENT_ENTITY: a_new_requirement_entity}
        update_learning_unit_year_with_report(self.learning_unit_year, {}, entities_to_update)
        self.assert_entity_has_not_changed(self.allocation_entity_container)
        self.assert_entity_has_not_changed(self.additional_entity_container_1)
        self.assert_entity_has_not_changed(self.additional_entity_container_2)

        self.assert_entity_has_been_modified(self.requirement_entity_container, a_new_requirement_entity)

    def test_with_all_entities_to_update(self):
        a_new_requirement_entity = EntityFactory()
        a_new_allocation_entity = EntityFactory()
        a_new_additional_entity_1 = EntityFactory()
        a_new_additional_entity_2 = EntityFactory()
        entities_to_update = {
            entity_container_year_link_type.REQUIREMENT_ENTITY: a_new_requirement_entity,
            entity_container_year_link_type.ALLOCATION_ENTITY: a_new_allocation_entity,
            entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1: a_new_additional_entity_1,
            entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2: a_new_additional_entity_2
        }

        update_learning_unit_year_with_report(self.learning_unit_year, {}, entities_to_update)

        self.assert_entity_has_been_modified(self.requirement_entity_container, a_new_requirement_entity)
        self.assert_entity_has_been_modified(self.allocation_entity_container, a_new_allocation_entity)
        self.assert_entity_has_been_modified(self.additional_entity_container_1, a_new_additional_entity_1)
        self.assert_entity_has_been_modified(self.additional_entity_container_2, a_new_additional_entity_2)

    def test_with_entity_set_to_none(self):
        entities_to_update = {entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2: None}
        update_learning_unit_year_with_report(self.learning_unit_year, {}, entities_to_update)
        self.assert_entity_has_not_changed(self.requirement_entity_container)
        self.assert_entity_has_not_changed(self.allocation_entity_container)
        self.assert_entity_has_not_changed(self.additional_entity_container_1)

        id_obj_deleted = self.additional_entity_container_2.id
        with self.assertRaises(ObjectDoesNotExist):
            EntityContainerYear.objects.get(id=id_obj_deleted)

    def test_with_entity_none_and_full_in(self):
        self.additional_entity_container_2.delete()

        a_new_additional_requirement_entity = EntityFactory()
        entities_to_update = {
            entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2: a_new_additional_requirement_entity
        }
        update_learning_unit_year_with_report(self.learning_unit_year, {}, entities_to_update)

        self.assertTrue(EntityContainerYear.objects.filter(
            entity=a_new_additional_requirement_entity,
            type=entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2,
            learning_container_year=self.learning_unit_year.learning_container_year
        ).exists())

    def test_apply_changes_to_next_learning_unit_year(self):
        a_learning_unit = self.setup_learning_unit(self.starting_academic_year.year)
        learning_unit_years = self.setup_list_of_learning_unit_years_full(
            self.list_of_academic_years_after_now,
            a_learning_unit,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )
        current_requirement_entity = EntityFactory()
        for luy in learning_unit_years:
            EntityContainerYearFactory(
                learning_container_year=luy.learning_container_year,
                entity=current_requirement_entity,
                type=entity_container_year_link_type.REQUIREMENT_ENTITY)

        a_new_requirement_entity = EntityFactory()
        entities_to_update = {entity_container_year_link_type.REQUIREMENT_ENTITY: a_new_requirement_entity}

        update_learning_unit_year_with_report(learning_unit_years[1], {}, entities_to_update,
                                              override_postponement_consistency=True)

        entity_container_luy_0 = EntityContainerYear.objects.get(
            learning_container_year=learning_unit_years[0].learning_container_year)
        self.assert_entity_has_not_changed(entity_container_luy_0)

        for luy in learning_unit_years[1:]:
            entity_container_luy = EntityContainerYear.objects.get(
                learning_container_year=luy.learning_container_year)
            self.assert_entity_has_been_modified(entity_container_luy, a_new_requirement_entity)

    def test_with_no_report(self):
        a_learning_unit = self.setup_learning_unit(self.starting_academic_year.year)
        learning_unit_years = self.setup_list_of_learning_unit_years_full(
            self.list_of_academic_years_after_now,
            a_learning_unit,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )
        current_requirement_entity = EntityFactory()
        for luy in learning_unit_years:
            EntityContainerYearFactory(
                learning_container_year=luy.learning_container_year,
                entity=current_requirement_entity,
                type=entity_container_year_link_type.REQUIREMENT_ENTITY)

        a_new_requirement_entity = EntityFactory()
        entities_to_update = {entity_container_year_link_type.REQUIREMENT_ENTITY: a_new_requirement_entity}

        update_learning_unit_year_with_report(learning_unit_years[0], {}, entities_to_update, with_report=False)

        entity_container_luy_0 = EntityContainerYear.objects.get(
            learning_container_year=learning_unit_years[0].learning_container_year)
        self.assert_entity_has_been_modified(entity_container_luy_0, a_new_requirement_entity)

        for luy in learning_unit_years[1:]:
            entity_container_luy = EntityContainerYear.objects.get(
                learning_container_year=luy.learning_container_year)
            self.assert_entity_has_not_changed(entity_container_luy)

    def assert_entity_has_not_changed(self, entity_container):
        past_entity = entity_container.entity
        entity_container.refresh_from_db()
        current_entity = entity_container.entity

        self.assertEqual(past_entity, current_entity)

    def assert_entity_has_been_modified(self, entity_container, expected_entity):
        entity_container.refresh_from_db()

        self.assertEqual(entity_container.entity, expected_entity)

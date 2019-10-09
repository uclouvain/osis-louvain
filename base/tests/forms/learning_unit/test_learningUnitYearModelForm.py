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
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_unit.learning_unit_create import CRUCIAL_YEAR_FOR_CREDITS_VALIDATION
from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.person import PersonFactory
from base.tests.forms.test_learning_unit_create_2 import get_valid_form_data


class TestCreditsValidation(TestCase):

    def setUp(self):
        start_year = AcademicYearFactory(year=CRUCIAL_YEAR_FOR_CREDITS_VALIDATION - 1)
        end_year = AcademicYearFactory(year=CRUCIAL_YEAR_FOR_CREDITS_VALIDATION + 1)
        self.academic_years = GenerateAcademicYear(start_year, end_year).academic_years
        self.learn_unit_structure = GenerateContainer(self.academic_years[0], self.academic_years[2])
        self.learning_unit_year_2017 = LearningUnitYear.objects.get(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year=self.academic_years[0]
        )
        self.learning_unit_year_2018 = LearningUnitYear.objects.get(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year=self.academic_years[1]
        )
        self.learning_unit_year_2019 = LearningUnitYear.objects.get(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year=self.academic_years[2]
        )
        self.person = PersonFactory()

    def test_credits_no_decimal_in_2018(self):
        form = self._build_form_with_decimal(self.learning_unit_year_2018)
        self._assert_not_valid(form)

    def test_credits_no_decimal_after_2018(self):
        form = self._build_form_with_decimal(self.learning_unit_year_2019)
        self._assert_not_valid(form)

    def test_credits_decimal_while_creating(self):
        form = self._build_form_with_decimal(None)
        self._assert_not_valid(form)

    def test_credits_decimal_accepted_before_2018(self):
        form = self._build_form_with_decimal(self.learning_unit_year_2017)
        self.assertTrue(form.is_valid())

    def _build_form_with_decimal(self, luy):
        ac = self.academic_years[1]
        if luy:
            ac = luy.academic_year
        data = get_valid_form_data(ac,
                                   self.person,
                                   learning_unit_year=luy)
        data.update({'credits': 2.5})
        form = LearningUnitYearModelForm(data=data, person=self.person, subtype=learning_unit_year_subtypes.FULL,
                                         instance=luy)
        return form

    def _assert_not_valid(self, form):
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(form.errors['credits'], [_('The credits value should be an integer')])

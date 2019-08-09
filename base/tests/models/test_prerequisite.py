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
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

import base.templatetags.prerequisite
from base.models import prerequisite
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory


class TestPrerequisiteSyntaxValidator(TestCase):
    def test_empty_string(self):
        self.assertIsNone(prerequisite.prerequisite_syntax_validator(""))

    def test_acronym_cannot_include_space(self):
        test_values = (
            "LSINF 1111",
            "LSINF 1256 B"
        )
        self.assert_raises_validation_error(test_values)

    def test_acronym_syntax(self):
        test_values = (
            "1452 LINGI",
            "LILKNLJLJFD48464",
            "LI12"
        )
        self.assert_raises_validation_error(test_values)

    def test_can_only_have_one_main_operator(self):
        test_values = (
            "LSINF1111 ET LINGI152 OU LINGI2356",
            "LSINF1111B OU LINGI152 ET LINGI2356",
        )
        self.assert_raises_validation_error(test_values)

    def test_main_and_secondary_operators_must_be_different(self):
        test_values = (
            "LSINF1111 ET (LINGI1526 ET LINGI2356)",
            "LSINF1111 OU (LINGI1526 OU LINGI2356)",
        )
        self.assert_raises_validation_error(test_values)

    def test_group_must_have_at_least_two_elements(self):
        test_values = (
            "LSINF1111 ET (LINGI152)",
        )
        self.assert_raises_validation_error(test_values)

    def test_cannot_have_unique_element_as_a_group(self):
        test_values = (
            "(LSINF1111 ET LINGI2315)",
        )
        self.assert_raises_validation_error(test_values)

    def assert_raises_validation_error(self, test_values):
        for test_value in test_values:
            with self.subTest(bad_prerequisite=test_value):
                with self.assertRaises(ValidationError):
                    prerequisite.prerequisite_syntax_validator(test_value)

    def test_with_prerequisites_correctly_encoded(self):
        test_values = (
            "LSINF1111 ET LINGI1452 ET LINGI2356",
            "LSINF1111 OU LINGI1452 OU LINGI2356",
            "LSINF1111 ET (LINGI1526B OU LINGI2356)",
            "LSINF1111 OU (LINGI1526 ET LINGI2356) OU (LINGI1552 ET LINGI2347)",
            "LSINF1111 ET (LINGI1152 OU LINGI1526 OU LINGI2356)",
            "(LINGI1526 ET LINGI2356) OU LINGI1552 OU LINGI2347",
            "LINGI2145",
            "LINGI2145A",
        )
        for test_value in test_values:
            with self.subTest(good_prerequisite=test_value):
                self.assertIsNone(prerequisite.prerequisite_syntax_validator(test_value))


class TestPrerequisiteString(TestCase):
    def test_get_acronym_as_href(self):
        current_academic_yr = create_current_academic_year()

        learning_unit_yr = LearningUnitYearFactory(academic_year=current_academic_yr)
        learning_unit_yr_prerequisite = LearningUnitYearFactory(academic_year=current_academic_yr)

        prerequisite_item = PrerequisiteItemFactory(
            prerequisite=PrerequisiteFactory(learning_unit_year=learning_unit_yr),
            learning_unit=learning_unit_yr_prerequisite.learning_unit
        )

        previous_academic_yr = AcademicYearFactory(year=current_academic_yr.year - 1)
        self.assertEqual(
            base.templatetags.prerequisite._get_acronym_as_href({}, prerequisite_item, previous_academic_yr),
            '')

        self.assertEqual(
            base.templatetags.prerequisite._get_acronym_as_href({}, prerequisite_item, current_academic_yr),
            _get_acronym_as_href(learning_unit_yr_prerequisite)
        )


def _get_acronym_as_href(luy):
    return "<a href='/learning_units/{}/' title=\"{}\n{} : {} / {}\">{}</a>".format(
        luy.id,
        luy.complete_title,
        _('Cred. rel./abs.'),
        '-',
        luy.credits.normalize(),
        luy.acronym
    )


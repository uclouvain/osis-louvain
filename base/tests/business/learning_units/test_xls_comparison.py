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
import datetime
from unittest import mock
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _
from base.tests.factories.user import UserFactory
from base.business.learning_units.xls_comparison import prepare_xls_content, \
    _get_learning_unit_yrs_on_2_different_years, _translate_status, create_xls_comparison, \
    XLS_FILENAME, XLS_DESCRIPTION, LEARNING_UNIT_TITLES, WORKSHEET_TITLE, CELLS_MODIFIED_NO_BORDER, DATA, \
    _check_changes_other_than_code_and_year, CELLS_TOP_BORDER
from osis_common.document import xls_build
from base.tests.factories.business.learning_units import GenerateContainer


class TestComparisonXls(TestCase):
    def setUp(self):
        self.user = UserFactory()
        generatorContainer = GenerateContainer(datetime.date.today().year-2, datetime.date.today().year)
        self.previous_learning_unit_year = generatorContainer.generated_container_years[0].learning_unit_year_full
        self.learning_unit_year_1 = generatorContainer.generated_container_years[1].learning_unit_year_full

        self.academic_year = self.learning_unit_year_1.academic_year
        self.previous_academic_year = self.previous_learning_unit_year.academic_year

    def test_prepare_xls_content_no_data(self):
        self.assertEqual(prepare_xls_content([]), {'data': [], CELLS_MODIFIED_NO_BORDER: None, CELLS_TOP_BORDER: None})

    def test_prepare_xls_content_with_data(self):
        learning_unit_years = _get_learning_unit_yrs_on_2_different_years(
            self.previous_academic_year.year,
            [self.learning_unit_year_1]
        )
        data_dict = prepare_xls_content(learning_unit_years)
        data = data_dict.get(DATA)
        self.assertEqual(len(data), 2)
        learning_unit_yr = self.previous_learning_unit_year
        self.assertEqual(data[0][0], learning_unit_yr.acronym)
        self.assertEqual(data[0][1], learning_unit_yr.academic_year.name)
        self.assertEqual(data[0][2], xls_build.translate(learning_unit_yr.learning_container_year.container_type))
        self.assertEqual(data[0][3], _translate_status(learning_unit_yr.status))
        self.assertEqual(data[0][4], xls_build.translate(learning_unit_yr.subtype))
        self.assertEqual(data[0][5],
                         str(_(learning_unit_yr.internship_subtype)) if learning_unit_yr.internship_subtype else '')
        self.assertEqual(data[0][6], learning_unit_yr.credits)
        self.assertEqual(data[0][7], learning_unit_yr.language.name if learning_unit_yr.language else '')
        self.assertEqual(data[0][8], str(_(learning_unit_yr.periodicity)) if learning_unit_yr.periodicity else '')
        self.assertEqual(data[0][9], str(_(learning_unit_yr.quadrimester)) if learning_unit_yr.quadrimester else '')
        self.assertEqual(data[0][10], str(_(learning_unit_yr.session)) if learning_unit_yr.session else '')
        self.assertEqual(data[0][11], learning_unit_yr.learning_container_year.common_title)
        self.assertEqual(data[0][12], learning_unit_yr.specific_title)
        self.assertEqual(data[0][13], learning_unit_yr.learning_container_year.common_title_english)
        self.assertEqual(data[0][14], learning_unit_yr.specific_title_english)

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_no_data(self, mock_generate_xls):
        create_xls_comparison(self.user, [], None, self.previous_academic_year.year)
        expected_argument = _generate_xls_build_parameter([], self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)

    def test_check_for_changes(self):
        learning_unit_yr_data = [
            ['acronym', '2016-17', 'credits', 'idem'],
            ['acronym 2', '2017-18', 'other credits', 'idem'],
        ]
        # C2 ('C' = third column, '2' = 2nd line)
        self.assertEqual(
            _check_changes_other_than_code_and_year(
                learning_unit_yr_data[0],
                learning_unit_yr_data[1],
                2),
            ['A2', 'C2'])


def _generate_xls_build_parameter(xls_data, user):
    return {
        xls_build.LIST_DESCRIPTION_KEY: _(XLS_DESCRIPTION),
        xls_build.FILENAME_KEY: _(XLS_FILENAME),
        xls_build.USER_KEY: user.username,
        xls_build.WORKSHEETS_DATA: [{
            xls_build.CONTENT_KEY: xls_data,
            xls_build.HEADER_TITLES_KEY: LEARNING_UNIT_TITLES,
            xls_build.WORKSHEET_TITLE_KEY: _(WORKSHEET_TITLE),
            xls_build.STYLED_CELLS: None,
            xls_build.COLORED_ROWS: None,
        }]
    }

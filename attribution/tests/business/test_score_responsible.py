##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

from django.test import TestCase

from attribution.business import score_responsible
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.user import UserFactory


class TestGetAttributionsData(TestCase):
    @mock.patch('attribution.business.score_responsible.get_learning_unit_year_managed_by_user_from_id')
    @mock.patch('attribution.models.attribution.find_all_responsible_by_learning_unit_year')
    def test_get_attributions_data(self, mock_find_all_responsible, mock_get_learning_unit):
        learning_unit_year = LearningUnitYearFactory()
        mock_get_learning_unit.return_value = learning_unit_year
        mock_find_all_responsible.return_value = []

        expected_result = {
            'learning_unit_year': learning_unit_year,
            'attributions': [],
            'academic_year': learning_unit_year.academic_year
        }
        result = score_responsible.get_attributions_data(
            UserFactory(),
            learning_unit_year.id,
            '-summary_responsible'
        )
        self.assertIsInstance(result, dict)
        self.assertDictEqual(result, expected_result)

# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from unittest.mock import patch

from django.test import SimpleTestCase

from learning_unit.ddd import command
from learning_unit.ddd.service.read import get_multiple_learning_unit_years_service


class TestGetMultipleLearningUnitYear(SimpleTestCase):
    def setUp(self):
        self.cmds = [
            command.GetLearningUnitYearCommand(year=2018, code="LTRON100B"),
            command.GetLearningUnitYearCommand(year=2018, code="LAGRO100B"),
            command.GetLearningUnitYearCommand(year=2018, code="LAGRO200B"),
        ]

    def test_assert_repository_called(self):
        with patch('learning_unit.ddd.service.read.get_multiple_learning_unit_years_service.load_learning_unit_year.'
                   'load_multiple_by_identity') as mock_repo_multiple:
            get_multiple_learning_unit_years_service.get_multiple_learning_unit_years(self.cmds)
            self.assertTrue(mock_repo_multiple.called)

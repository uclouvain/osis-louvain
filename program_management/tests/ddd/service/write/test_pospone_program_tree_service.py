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
import mock
from django.test import TestCase

from program_management.ddd import command
from program_management.ddd.domain import program_tree
from program_management.ddd.service.write import postpone_program_tree_service


class TestPostponeProgramTree(TestCase):
    @mock.patch("program_management.ddd.domain.service.calculate_end_postponement."
                "CalculateEndPostponement.calculate_year_of_end_postponement", return_value=2021)
    @mock.patch("program_management.ddd.service.write.copy_program_tree_service.copy_program_tree_to_next_year")
    def test_should_return_a_number_of_identities_equal_to_difference_of_from_year_and_until_year(
            self,
            mock_copy_program_to_next_year,
            mock_calculate_end_year_of_postponement):

        program_tree_identities = [
            program_tree.ProgramTreeIdentity("CODE", year=2018),
            program_tree.ProgramTreeIdentity("CODE", year=2019),
            program_tree.ProgramTreeIdentity("CODE", year=2020)
        ]
        mock_copy_program_to_next_year.side_effect = program_tree_identities
        mock_calculate_end_year_of_postponement.return_value = 2021

        cmd = command.PostponeProgramTreeCommand(
            from_year=2018,
            from_code="CODE",
            offer_acronym="ACRONYM"
        )
        result = postpone_program_tree_service.postpone_program_tree(cmd)

        self.assertListEqual(program_tree_identities, result)

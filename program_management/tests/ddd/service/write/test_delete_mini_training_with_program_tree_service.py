#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import skip

import attr
import mock

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from education_group.ddd.command import GetMiniTrainingCommand
from education_group.ddd.domain.exception import MiniTrainingHaveEnrollments, \
    MiniTrainingHaveLinkWithEPC
from education_group.ddd.service.read import get_mini_training_service
from education_group.tests.factories.mini_training import MiniTrainingFactory
from program_management.ddd.command import DeleteMiniTrainingWithProgramTreeCommand
from program_management.ddd.domain.exception import ProgramTreeNonEmpty
from program_management.ddd.service.write import delete_mini_training_with_program_tree_service
from program_management.tests.ddd.factories.domain.program_tree_version.mini_training.MINECON import MINECONFactory
from testing.testcases import DDDTestCase


class DeleteMiniTrainingWithProgramTreeTestCase(DDDTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.minecon = MINECONFactory()
        [MiniTrainingFactory.from_node(tree_version.get_tree().root_node) for tree_version in self.minecon[1:]]
        self.minecon = self.minecon[0]
        self.minecon_mini_training = get_mini_training_service.get_mini_training(
            GetMiniTrainingCommand(acronym=self.minecon.entity_id.offer_acronym, year=self.minecon.entity_id.year)
        )

        self.cmd = DeleteMiniTrainingWithProgramTreeCommand(
            code=self.minecon.program_tree_identity.code,
            offer_acronym=self.minecon.entity_id.offer_acronym,
            version_name=self.minecon.version_name,
            transition_name=self.minecon.transition_name,
            from_year=self.minecon.entity_id.year + 2
        )

    @mock.patch(
        "education_group.ddd.domain.service.enrollment_counter.EnrollmentCounter.get_mini_training_enrollments_count",
        return_value=5
    )
    def test_cannot_delete_mini_training_for_which_there_is_enrolments(self, mock_get_enrollments_count):
        with self.assertRaisesBusinessException(MiniTrainingHaveEnrollments):
            delete_mini_training_with_program_tree_service.delete_mini_training_with_program_tree(self.cmd)

    @mock.patch(
        "education_group.ddd.domain.service.link_with_epc.LinkWithEPC.is_mini_training_have_link_with_epc",
        return_value=True
    )
    def test_cannot_delete_mini_training_for_which_there_is_enrolments(self, mock_has_mini_training_a_link_with_epc):
        with self.assertRaisesBusinessException(MiniTrainingHaveLinkWithEPC):
            delete_mini_training_with_program_tree_service.delete_mini_training_with_program_tree(self.cmd)

    @skip("TODO")
    def test_cannot_delete_training_which_is_used_in_another_program(self):
        pass

    def test_cannot_delete_non_empty_program_tree(self):
        cmd = attr.evolve(self.cmd, from_year=self.minecon.entity_id.year)

        with self.assertRaisesBusinessException(ProgramTreeNonEmpty):
            delete_mini_training_with_program_tree_service.delete_mini_training_with_program_tree(cmd)

    @skip("Broken service do not take into account new end year")
    def test_cannot_delete_standard_version_if_specific_version_exists_during_those_years(self):
        MINECONFactory.create_specific_version_from_tree_version(self.minecon)

        with self.assertRaisesBusinessException(MultipleBusinessExceptions):
            delete_mini_training_with_program_tree_service.delete_mini_training_with_program_tree(self.cmd)

    @skip("Broken service do not take into account new end year")
    def test_cannot_delete_standard_version_if_transition_version_exists_during_those_years(self):
        MINECONFactory.create_transition_from_tree_version(self.minecon)

        with self.assertRaisesBusinessException(MultipleBusinessExceptions):
            delete_mini_training_with_program_tree_service.delete_mini_training_with_program_tree(self.cmd)

    def test_should_return_mini_training_identities(self):
        result = delete_mini_training_with_program_tree_service.delete_mini_training_with_program_tree(self.cmd)

        expected = [
            attr.evolve(self.minecon_mini_training.entity_id, year=year)
            for year in range(self.cmd.from_year, 2026)
        ]
        self.assertEqual(expected, result)

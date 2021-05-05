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

import attr

from program_management.ddd.command import DeletePermanentlyMiniTrainingStandardVersionCommand
from program_management.ddd.domain.exception import ProgramTreeNonEmpty
from program_management.ddd.service.write import delete_all_mini_training_versions_service
from program_management.tests.ddd.factories.domain.program_tree_version.mini_training.MINECON import MINECONFactory
from program_management.tests.ddd.factories.domain.program_tree_version.mini_training.empty import \
    EmptyMiniTrainingFactory
from testing.testcases import DDDTestCase


class DeletePermanentlyMiniTrainingStandardVersion(DDDTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.mini_trainings = EmptyMiniTrainingFactory()
        self.mini_training = self.mini_trainings[0]

        self.cmd = DeletePermanentlyMiniTrainingStandardVersionCommand(
            acronym=self.mini_training.entity_id.offer_acronym,
            year=self.mini_training.entity_id.year + 1
        )

    def test_cannot_delete_non_empty_mini_training(self):
        minecon = MINECONFactory()[0]
        cmd = attr.evolve(
            self.cmd,
            acronym=minecon.entity_id.offer_acronym
        )

        with self.assertRaisesBusinessException(ProgramTreeNonEmpty):
            delete_all_mini_training_versions_service.delete_permanently_mini_training_standard_version(cmd)

    def test_return_mini_training_identities(self):
        result = delete_all_mini_training_versions_service.delete_permanently_mini_training_standard_version(self.cmd)

        expected = [mini_training.entity_id for mini_training in self.mini_trainings]
        self.assertListEqual(expected, result)

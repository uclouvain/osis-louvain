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

from program_management.ddd import command
from program_management.ddd.domain.exception import CannotDeleteSpecificVersionDueToTransitionVersionEndDate
from program_management.ddd.service.read import get_program_tree_version_service
from program_management.ddd.service.write import delete_all_specific_versions_service
from program_management.tests.ddd.factories.domain.program_tree_version.training.empty import EmptyTrainingFactory
from testing.testcases import DDDTestCase


class TestDeleteAllProgramTreeVersions(DDDTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tree_versions = EmptyTrainingFactory()
        self.specific_versions = EmptyTrainingFactory.create_specific_version_from_tree_version(self.tree_versions[0])
        self.cmd = command.DeletePermanentlyTreeVersionCommand(
            acronym=self.specific_versions[0].entity_id.offer_acronym,
            version_name=self.specific_versions[0].version_name,
            transition_name=self.specific_versions[0].transition_name,
        )

    def test_cannot_delete_tree_version_if_transition_version_exists(self):
        EmptyTrainingFactory.create_transition_from_tree_version(self.specific_versions[0])

        with self.assertRaisesBusinessException(CannotDeleteSpecificVersionDueToTransitionVersionEndDate):
            delete_all_specific_versions_service.delete_permanently_tree_version(self.cmd)

    def test_should_return_program_tree_version_identity(self):
        result = delete_all_specific_versions_service.delete_permanently_tree_version(self.cmd)

        expected = [tree_version.entity_id for tree_version in self.specific_versions]
        self.assertListEqual(expected, result)

    def test_should_delete_tree_version(self):
        tree_version_identities_deleted = delete_all_specific_versions_service.delete_permanently_tree_version(self.cmd)

        for tree_version_identity in tree_version_identities_deleted:
            with self.subTest(identity=tree_version_identity):
                self.assertIsNone(
                    get_program_tree_version_service.get_program_tree_version(
                        command.GetProgramTreeVersionCommand(
                            year=tree_version_identity.year,
                            acronym=tree_version_identity.offer_acronym,
                            version_name=tree_version_identity.version_name,
                            transition_name=tree_version_identity.transition_name
                        )
                    ))

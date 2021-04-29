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

from ddd.logic.shared_kernel.academic_year.builder.academic_year_identity_builder import AcademicYearIdentityBuilder
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear
from education_group.ddd.repository.training import TrainingRepository
from education_group.tests.ddd.factories.training import TrainingFactory
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository
from program_management.ddd.service.write import postpone_training_and_program_tree_modifications_service
from program_management.tests.ddd.factories.commands.postpone_training_and_root_group_modification_with_program_tree \
    import PostponeTrainingAndRootGroupModificationWithProgramTreeCommandFactory


class TestPostponeTrainingAndProgramTreeModificationsService(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.offer_year = 2020
        cls.cmd = PostponeTrainingAndRootGroupModificationWithProgramTreeCommandFactory(
            code="LDROI1200M",
            postpone_from_acronym="DROI2M",
            postpone_from_year=cls.offer_year
        )

    def setUp(self):
        self.postpone_training_and_group_modification_patcher = mock.patch(
            "program_management.ddd.service.write"
            ".postpone_training_and_program_tree_modifications_service."
            "postpone_training_and_group_modification_service.postpone_training_and_group_modification",
            return_value=[]
        )
        self.mocked_postpone_training_and_group_modification = \
            self.postpone_training_and_group_modification_patcher.start()
        self.addCleanup(self.postpone_training_and_group_modification_patcher.stop)

        self.postpone_pgrm_tree_patcher = mock.patch(
            "program_management.ddd.service.write."
            "postpone_training_and_program_tree_modifications_service."
            "postpone_program_tree_service.postpone_program_tree",
            return_value=[]
        )
        self.mocked_postpone_pgrm_tree = self.postpone_pgrm_tree_patcher.start()
        self.addCleanup(self.postpone_pgrm_tree_patcher.stop)

        self.postpone_pgrm_tree_version_patcher = mock.patch(
            "program_management.ddd.service.write."
            "postpone_training_and_program_tree_modifications_service."
            "postpone_tree_specific_version_service.postpone_program_tree_version",
            return_value=[]
        )
        self.mocked_postpone_pgrm_tree_version = self.postpone_pgrm_tree_version_patcher.start()
        self.addCleanup(self.postpone_pgrm_tree_version_patcher.stop)

        self.update_version_end_date_patcher = mock.patch(
            "program_management.ddd.service.write.update_program_tree_version_end_date_service."
            "update_program_tree_version_end_date"
        )
        self.mocked_update_version_end_date = self.update_version_end_date_patcher.start()
        self.addCleanup(self.update_version_end_date_patcher.stop)

        self.update_training_and_group_patcher = mock.patch(
            "education_group.ddd.service.write.update_training_and_group_service."
            "update_training_and_group"
        )
        self.mocked_update_training_and_group = self.update_training_and_group_patcher.start()
        self.addCleanup(self.update_training_and_group_patcher.stop)

        self.mock_anac_repository = mock.create_autospec(AcademicYearRepository)
        current_anac = AcademicYear(
            entity_id=AcademicYearIdentityBuilder.build_from_year(year=self.offer_year - 1),
            start_date=None,
            end_date=None
        )
        self.mock_anac_repository.get_current.return_value = current_anac
        self.mock_training_repository = mock.create_autospec(TrainingRepository)
        self.mock_training_repository.get.return_value = TrainingFactory(end_year=None)

    def test_assert_call_multiple_service(self):
        postpone_training_and_program_tree_modifications_service. \
            postpone_training_and_program_tree_modifications(
            self.cmd,
            self.mock_anac_repository,
            self.mock_training_repository
        )

        self.assertTrue(self.mocked_postpone_training_and_group_modification.called)
        self.assertTrue(self.mocked_postpone_pgrm_tree.called)
        self.assertTrue(self.mocked_postpone_pgrm_tree_version.called)
        self.assertTrue(self.mocked_update_version_end_date.called)

    def test_assert_call_not_postponement_services_if_in_past(self):
        current_anac = AcademicYear(
            entity_id=AcademicYearIdentityBuilder.build_from_year(year=self.offer_year + 1),
            start_date=None,
            end_date=None
        )
        self.mock_anac_repository.get_current.return_value = current_anac
        postpone_training_and_program_tree_modifications_service. \
            postpone_training_and_program_tree_modifications(
            self.cmd,
            self.mock_anac_repository,
            self.mock_training_repository
        )

        self.assertFalse(self.mocked_postpone_training_and_group_modification.called)
        self.assertFalse(self.mocked_postpone_pgrm_tree.called)
        self.assertFalse(self.mocked_postpone_pgrm_tree_version.called)

        self.assertTrue(self.mocked_update_version_end_date.called)
        self.assertTrue(self.mocked_update_training_and_group.called)

    def test_assert_call_postponement_services_if_in_past_but_end_year_changed(self):
        current_anac = AcademicYear(
            entity_id=AcademicYearIdentityBuilder.build_from_year(year=self.offer_year + 1),
            start_date=None,
            end_date=None
        )
        self.mock_anac_repository.get_current.return_value = current_anac
        self.mock_training_repository.get.return_value = TrainingFactory(end_year=2025)
        postpone_training_and_program_tree_modifications_service \
            .postpone_training_and_program_tree_modifications(
            self.cmd,
            self.mock_anac_repository,
            self.mock_training_repository
        )

        self.assertTrue(self.mocked_postpone_training_and_group_modification.called)
        self.assertTrue(self.mocked_postpone_pgrm_tree.called)
        self.assertTrue(self.mocked_postpone_pgrm_tree_version.called)
        self.assertTrue(self.mocked_update_version_end_date.called)

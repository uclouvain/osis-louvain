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

from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.schedule_type import ScheduleTypeEnum
from ddd.logic.shared_kernel.academic_year.builder.academic_year_identity_builder import AcademicYearIdentityBuilder
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear
from education_group.ddd.repository.mini_training import MiniTrainingRepository
from education_group.tests.factories.mini_training import MiniTrainingFactory
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository
from program_management.ddd import command
from program_management.ddd.service.write import \
    postpone_mini_training_and_program_tree_modifications_service


class TestPostponeMiniTrainingAndProgramTreeModifications(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.offer_year = 2020
        cls.cmd = command.PostponeMiniTrainingAndRootGroupModificationWithProgramTreeCommand(
            year=cls.offer_year,
            code="LTRONC1000",
            abbreviated_title="TRONCCOMMUN",
            title_fr="Tronc commun",
            title_en="Common core",
            credits=20,
            constraint_type=ConstraintTypeEnum.CREDITS.name,
            min_constraint=0,
            max_constraint=10,
            management_entity_acronym="DRT",
            teaching_campus_name="Mons Fucam",
            organization_name="UCLouvain",
            remark_fr="Remarque en français",
            remark_en="Remarque en anglais",
            end_year=None,
            keywords="A key",
            schedule_type=ScheduleTypeEnum.DAILY.name,
            status=ActiveStatusEnum.ACTIVE.name,
            teaching_campus_organization_name="Fucam"
        )

    def setUp(self):
        self.postpone_mini_training_and_orphan_group_modifications_patcher = mock.patch(
            "program_management.ddd.service.write."
            "postpone_mini_training_and_program_tree_modifications_service."
            "postpone_mini_training_and_orphan_group_modifications_service."
            "postpone_mini_training_and_orphan_group_modifications",
            return_value=[]
        )
        self.mocked_postpone_mini_training_and_orphan_group_modifications = \
            self.postpone_mini_training_and_orphan_group_modifications_patcher.start()
        self.addCleanup(self.postpone_mini_training_and_orphan_group_modifications_patcher.stop)

        self.postpone_pgrm_tree_patcher = mock.patch(
            "program_management.ddd.service.write."
            "postpone_mini_training_and_program_tree_modifications_service."
            "postpone_program_tree_service.postpone_program_tree",
            return_value=[]
        )
        self.mocked_postpone_pgrm_tree = self.postpone_pgrm_tree_patcher.start()
        self.addCleanup(self.postpone_pgrm_tree_patcher.stop)

        self.postpone_pgrm_tree_version_patcher = mock.patch(
            "program_management.ddd.service.write."
            "postpone_mini_training_and_program_tree_modifications_service."
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

        self.update_mini_training_and_group_patcher = mock.patch(
            "education_group.ddd.service.write.update_mini_training_and_group_service."
            "update_mini_training_and_group"
        )
        self.mocked_update_mini_training_and_group = self.update_mini_training_and_group_patcher.start()
        self.addCleanup(self.update_mini_training_and_group_patcher.stop)

        self.mock_anac_repository = mock.create_autospec(AcademicYearRepository)
        current_anac = AcademicYear(
            entity_id=AcademicYearIdentityBuilder.build_from_year(year=self.offer_year - 1),
            start_date=None,
            end_date=None
        )
        self.mock_anac_repository.get_current.return_value = current_anac

        self.mock_minitraining_repository = mock.create_autospec(MiniTrainingRepository)
        self.mock_minitraining_repository.get.return_value = MiniTrainingFactory()

    def test_assert_call_multiple_service(self):
        postpone_mini_training_and_program_tree_modifications_service \
            .postpone_mini_training_and_program_tree_modifications(
            self.cmd,
            self.mock_anac_repository,
            self.mock_minitraining_repository
        )

        self.assertTrue(self.mocked_postpone_mini_training_and_orphan_group_modifications.called)
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
        postpone_mini_training_and_program_tree_modifications_service. \
            postpone_mini_training_and_program_tree_modifications(
            self.cmd,
            self.mock_anac_repository,
            self.mock_minitraining_repository
        )

        self.assertFalse(self.mocked_postpone_mini_training_and_orphan_group_modifications.called)
        self.assertFalse(self.mocked_postpone_pgrm_tree.called)
        self.assertFalse(self.mocked_postpone_pgrm_tree_version.called)

        self.assertTrue(self.mocked_update_version_end_date.called)
        self.assertTrue(self.mocked_update_mini_training_and_group.called)

    def test_assert_call_postponement_services_if_in_past_but_end_year_changed(self):
        current_anac = AcademicYear(
            entity_id=AcademicYearIdentityBuilder.build_from_year(year=self.offer_year + 1),
            start_date=None,
            end_date=None
        )
        self.mock_anac_repository.get_current.return_value = current_anac
        self.mock_minitraining_repository.get.return_value = MiniTrainingFactory(end_year=2025)
        postpone_mini_training_and_program_tree_modifications_service \
            .postpone_mini_training_and_program_tree_modifications(
            self.cmd,
            self.mock_anac_repository,
            self.mock_minitraining_repository
        )

        self.assertTrue(self.mocked_postpone_mini_training_and_orphan_group_modifications.called)
        self.assertTrue(self.mocked_postpone_pgrm_tree.called)
        self.assertTrue(self.mocked_postpone_pgrm_tree_version.called)
        self.assertTrue(self.mocked_update_version_end_date.called)

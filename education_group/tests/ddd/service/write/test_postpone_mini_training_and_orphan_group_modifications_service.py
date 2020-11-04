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
from unittest import mock

from django.test import TestCase

from education_group.ddd.domain.exception import MiniTrainingCopyConsistencyException
from education_group.ddd.service.write import postpone_mini_training_and_orphan_group_modifications_service
from education_group.tests.ddd.factories.command.postpone_mini_training_and_group_modification_command import \
    PostponeMiniTrainingAndGroupModificationCommandFactory


class TestPostponeMiniTrainingAndOrphanGroupModificationsService(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.cmd = PostponeMiniTrainingAndGroupModificationCommandFactory(
            postpone_from_year=2020
        )

    @mock.patch('education_group.ddd.service.write.postpone_mini_training_and_orphan_group_modifications_service.'
                'ConflictedFields.get_mini_training_conflicted_fields')
    @mock.patch('education_group.ddd.service.write.postpone_mini_training_and_orphan_group_modifications_service.'
                'update_mini_training_and_group_service.update_mini_training_and_group')
    @mock.patch('education_group.ddd.service.write.postpone_mini_training_and_orphan_group_modifications_service.'
                'CalculateEndPostponement.calculate_end_postponement_year_mini_training')
    @mock.patch('education_group.ddd.service.write.postpone_mini_training_and_orphan_group_modifications_service.'
                'copy_mini_training_service.copy_mini_training_to_next_year')
    @mock.patch('education_group.ddd.service.write.copy_group_service.copy_group')
    def test_ensure_consistency_error_not_stop_creating_training_when_end_postponement_is_undefined(
            self,
            mock_copy_group_to_next_year_service,
            mock_copy_mini_training_to_next_year_service,
            mock_calculate_end_postponement_year,
            mock_update_mini_training_and_group_service,
            mock_get_conflicted_fields
    ):
        mock_calculate_end_postponement_year.return_value = 2025
        mock_get_conflicted_fields.return_value = {2013: ['credits', 'titles']}

        with self.assertRaises(MiniTrainingCopyConsistencyException):
            postpone_mini_training_and_orphan_group_modifications_service.\
                postpone_mini_training_and_orphan_group_modifications(self.cmd)

        self.assertEqual(mock_update_mini_training_and_group_service.call_count, 1)
        self.assertEqual(mock_copy_mini_training_to_next_year_service.call_count, 5)
        self.assertEqual(mock_copy_group_to_next_year_service.call_count, 5)
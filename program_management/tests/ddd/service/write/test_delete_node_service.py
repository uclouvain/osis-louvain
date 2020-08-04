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

from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from education_group.ddd.domain.training import TrainingIdentity
from program_management.ddd import command
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity
from program_management.ddd.service.write import delete_node_service


class TestDeleteNodeService(TestCase):
    def setUp(self):
        self.delete_orphan_group_patcher = mock.patch(
            "program_management.ddd.service.write.delete_node_service.delete_orphan_group_service.delete_orphan_group",
            return_value=None
        )
        self.mocked_delete_orphan_group = self.delete_orphan_group_patcher.start()
        self.addCleanup(self.delete_orphan_group_patcher.stop)

        self.delete_orphan_training_patcher = mock.patch(
            "program_management.ddd.service.write.delete_node_service."
            "delete_orphan_training_service.delete_orphan_training",
            return_value=None
        )
        self.mocked_delete_orphan_training = self.delete_orphan_training_patcher.start()
        self.addCleanup(self.delete_orphan_training_patcher.stop)

        self.delete_orphan_mini_training_patcher = mock.patch(
            "program_management.ddd.service.write.delete_node_service."
            "delete_orphan_mini_training_service.delete_orphan_mini_training",
            return_value=None
        )
        self.mocked_delete_orphan_mini_training = self.delete_orphan_mini_training_patcher.start()
        self.addCleanup(self.delete_orphan_mini_training_patcher.stop)

    def test_assert_delete_node_of_type_group_called_delete_orphan_group(self):
        cmd = command.DeleteNodeCommand(code="LDROI1000", year=2018, node_type=GroupType.SUB_GROUP.name)
        delete_node_service.delete_node(cmd)

        self.assertTrue(self.mocked_delete_orphan_group.called)
        self.assertFalse(self.mocked_delete_orphan_training.called)
        self.assertFalse(self.mocked_delete_orphan_mini_training.called)

    @mock.patch("program_management.ddd.service.write.delete_node_service.ProgramTreeVersionIdentitySearch"
                ".get_from_node_identity")
    def test_assert_delete_node_of_type_mini_training_called_delete_orphan_mini_training(self, mock_search_id):
        mock_search_id.return_value = ProgramTreeVersionIdentity(
            offer_acronym="MINITRAINING",
            year=2018,
            version_name='',
            is_transition=False
        )
        cmd = command.DeleteNodeCommand(code="OPT100M", year=2018, node_type=MiniTrainingType.OPTION.name)
        delete_node_service.delete_node(cmd)

        self.assertTrue(self.mocked_delete_orphan_mini_training.called)
        self.assertFalse(self.mocked_delete_orphan_group.called)
        self.assertFalse(self.mocked_delete_orphan_training.called)

    @mock.patch("program_management.ddd.service.write.delete_node_service.TrainingIdentitySearch"
                ".get_from_node_identity")
    def test_assert_delete_node_of_type_training_called_delete_orphan_training(self, mock_search_training_id):
        mock_search_training_id.return_value = TrainingIdentity(acronym="TRAINING", year=2018)
        cmd = command.DeleteNodeCommand(code="OPT100M", year=2018, node_type=TrainingType.BACHELOR.name)
        delete_node_service.delete_node(cmd)

        self.assertTrue(self.mocked_delete_orphan_training.called)
        self.assertFalse(self.mocked_delete_orphan_mini_training.called)
        self.assertFalse(self.mocked_delete_orphan_group.called)

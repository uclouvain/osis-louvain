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

from education_group.ddd.domain import training
from education_group.tests.ddd.factories.command.create_training_command import CreateTrainingCommandFactory
from program_management.ddd.domain import program_tree, program_tree_version
from program_management.ddd.service.write import create_training_with_program_tree


class TestCreateAndReportTrainingWithProgramTree(TestCase):
    @mock.patch("program_management.ddd.service.write.postpone_tree_version_service.postpone_program_tree_version")
    @mock.patch("program_management.ddd.service.write.create_standard_version_service.create_standard_program_version")
    @mock.patch("program_management.ddd.service.write.postpone_program_tree_service.postpone_program_tree")
    @mock.patch("program_management.ddd.service.write.create_standard_program_tree_service.create_standard_program_tree")
    @mock.patch("education_group.ddd.service.write.create_group_service.create_orphan_group")
    @mock.patch("education_group.ddd.service.write.create_orphan_training_service.create_and_postpone_orphan_training")
    def test_should_create_trainings_until_postponement_limit(
            self,
            mock_create_and_postpone_orphan_training,
            mock_create_orphan_group,
            mock_create_standard_program_tree,
            mock_postpone_program_tree,
            mock_create_standard_program_version,
            mock_postpone_program_tree_version):

        training_identities = [
            training.TrainingIdentity(acronym="ACRONYM", year=2020),
            training.TrainingIdentity(acronym="ACRONYM", year=2021),
            training.TrainingIdentity(acronym="ACRONYM", year=2022)
        ]

        mock_create_and_postpone_orphan_training.return_value = training_identities
        mock_create_orphan_group.return_value = None
        mock_create_standard_program_tree.return_value = program_tree.ProgramTreeIdentity(code="CODE", year=2020)
        mock_postpone_program_tree.return_value = None
        mock_create_standard_program_version.return_value = program_tree_version.ProgramTreeVersionIdentity(
            offer_acronym="Offer",
            year=2020,
            version_name="",
            is_transition=False,
        )
        mock_postpone_program_tree_version.return_value = None

        cmd = CreateTrainingCommandFactory()
        result = create_training_with_program_tree.create_and_report_training_with_program_tree(cmd)

        self.assertListEqual(training_identities, result)
        self.assertTrue(mock_create_and_postpone_orphan_training.called)
        self.assertTrue(mock_create_orphan_group.called)
        self.assertTrue(mock_create_standard_program_tree.called)
        self.assertTrue(mock_postpone_program_tree.called)
        self.assertTrue(mock_create_standard_program_version.called)
        self.assertTrue(mock_postpone_program_tree_version.called)

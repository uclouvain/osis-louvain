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

from base.tests.factories.academic_year import AcademicYearFactory
from education_group.tests.ddd.factories.repository.fake import get_fake_training_repository
from education_group.tests.ddd.factories.training import TrainingFactory
from program_management.ddd.domain.program_tree_version import STANDARD
from program_management.ddd.domain.service.calculate_end_postponement import CalculateEndPostponement
from program_management.tests.ddd.factories.commands.get_end_postponement_year_command import \
    GetEndPostponementYearCommandFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from program_management.tests.ddd.factories.repository.fake import get_fake_program_tree_repository, \
    get_fake_program_tree_version_repository
from testing.mocks import MockPatcherMixin


class TestCalculateEndPostponementYearAsTraining(MockPatcherMixin, TestCase):

    def setUp(self):
        self.current_year = 2020
        self.maximum_postponement_year = 2025
        academic_years = AcademicYearFactory.produce_in_future(self.current_year - 1)

        self.root_node_code = 'LDROI200M'

        self.program_tree = ProgramTreeFactory(
            entity_id__year=self.current_year,
            entity_id__code=self.root_node_code,
        )
        self.fake_program_tree_repository = get_fake_program_tree_repository([self.program_tree])

        self.program_tree_version = ProgramTreeVersionFactory(
            tree=self.program_tree,
            entity_id__version_name=STANDARD,
            program_tree_repository=self.fake_program_tree_repository
        )
        self.fake_program_tree_version_repository = get_fake_program_tree_version_repository(
            [self.program_tree_version]
        )

        self.command = GetEndPostponementYearCommandFactory(
            code=self.root_node_code,
            year=self.current_year,
        )

        self.mock_get_starting_academic_year(academic_years)

    def mock_get_starting_academic_year(self, academic_years):
        patcher = mock.patch("base.models.academic_year.starting_academic_year", return_value=academic_years[0])
        mock_starting_academic_year = patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch("program_management.ddd.domain.service.identity_search._get_data_from_db")
    def test_when_root_node_is_training_and_end_year_is_none(self, mock_data_from_db):
        training = TrainingFactory(entity_identity__year=self.current_year, end_year=None)
        mock_data_from_db.return_value = {
            "offer_acronym": training.entity_identity.acronym,
            "offer_type": training.type.name
        }
        fake_training_repository = get_fake_training_repository([training])
        result = CalculateEndPostponement.calculate_program_tree_end_postponement(
            identity=self.program_tree.entity_id,
            training_repository=fake_training_repository,
            mini_training_repository=None
        )
        self.assertEqual(result, self.maximum_postponement_year)

    @mock.patch("program_management.ddd.domain.service.identity_search._get_data_from_db")
    def test_when_root_node_is_training_and_end_year_gt_maximum_postponement(self, mock_data_from_db):
        end_year = self.maximum_postponement_year + 5
        training = TrainingFactory(entity_identity__year=self.current_year, end_year=end_year)
        mock_data_from_db.return_value = {
            "offer_acronym": training.entity_identity.acronym,
            "offer_type": training.type.name
        }
        fake_training_repository = get_fake_training_repository([training])
        result = CalculateEndPostponement.calculate_program_tree_end_postponement(
            identity=self.program_tree.entity_id,
            training_repository=fake_training_repository,
            mini_training_repository=None
        )
        self.assertEqual(result, self.maximum_postponement_year)

    @mock.patch("program_management.ddd.domain.service.identity_search._get_data_from_db")
    def test_when_root_node_is_training_and_end_year_lt_maximum_postponement(self, mock_data_from_db):
        end_year = self.maximum_postponement_year - 3
        training = TrainingFactory(entity_identity__year=self.current_year, end_year=end_year)
        mock_data_from_db.return_value = {
            "offer_acronym": training.entity_identity.acronym,
            "offer_type": training.type.name
        }
        fake_training_repository = get_fake_training_repository([training])
        result = CalculateEndPostponement.calculate_program_tree_end_postponement(
            identity=self.program_tree.entity_id,
            training_repository=fake_training_repository,
            mini_training_repository=None
        )
        self.assertEqual(result, end_year)

    @mock.patch("program_management.ddd.domain.service.identity_search._get_data_from_db")
    def test_when_root_node_is_training_and_end_year_equals_maximum_postponement(self, mock_data_from_db):
        end_year = self.maximum_postponement_year
        training = TrainingFactory(entity_identity__year=self.current_year, end_year=end_year)
        mock_data_from_db.return_value = {
            "offer_acronym": training.entity_identity.acronym,
            "offer_type": training.type.name
        }
        fake_training_repository = get_fake_training_repository([training])
        result = CalculateEndPostponement.calculate_program_tree_end_postponement(
            identity=self.program_tree.entity_id,
            training_repository=fake_training_repository,
            mini_training_repository=None
        )
        self.assertEqual(result, self.maximum_postponement_year)

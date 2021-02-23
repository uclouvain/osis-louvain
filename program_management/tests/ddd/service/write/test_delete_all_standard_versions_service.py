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
from mock import call

from education_group.tests.ddd.factories.training import TrainingFactory
from program_management.ddd import command
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity, STANDARD, NOT_A_TRANSITION
from program_management.ddd.service.write import delete_all_standard_versions_service


class TestDeleteAllStandardVersionsService(TestCase):
    def setUp(self):
        self.training = TrainingFactory()

        self.delete_standard_version_service_patcher = mock.patch(
            "program_management.ddd.service.write.delete_training_standard_version_service."
            "delete_training_standard_version",
            return_value=[]
        )
        self.mocked_delete_standard_version_service = self.delete_standard_version_service_patcher.start()
        self.addCleanup(self.delete_standard_version_service_patcher.stop)

    @mock.patch("program_management.ddd.domain.service.identity_search.ProgramTreeVersionIdentitySearch."
                "get_all_program_tree_version_identities")
    def test_assert_delete_delete_standard_version_service_called(self, mock_get_all_program_tree_version):
        mock_get_all_program_tree_version.return_value = [
            ProgramTreeVersionIdentity(year=2017, offer_acronym=self.training.acronym, version_name=STANDARD,
                                       transition_name=NOT_A_TRANSITION),
            ProgramTreeVersionIdentity(year=2018, offer_acronym=self.training.acronym, version_name=STANDARD,
                                       transition_name=NOT_A_TRANSITION),
            ProgramTreeVersionIdentity(year=2019, offer_acronym="NEWONE", version_name=STANDARD,
                                       transition_name=NOT_A_TRANSITION),
        ]

        cmd = command.DeletePermanentlyTrainingStandardVersionCommand(
            acronym=self.training.acronym,
            year=self.training.year
        )
        delete_all_standard_versions_service.delete_permanently_training_standard_version(cmd)

        expected_calls = [
            call(command.DeleteTrainingStandardVersionCommand(offer_acronym=self.training.acronym, year=2017)),
            call(command.DeleteTrainingStandardVersionCommand(offer_acronym=self.training.acronym, year=2018)),
            call(command.DeleteTrainingStandardVersionCommand(offer_acronym="NEWONE", year=2019))
        ]
        self.mocked_delete_standard_version_service.assert_has_calls(expected_calls)

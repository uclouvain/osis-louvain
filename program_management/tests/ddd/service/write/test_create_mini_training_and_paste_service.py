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
from django.test import SimpleTestCase, TestCase

from education_group.ddd.domain import mini_training
from program_management.ddd import command
from program_management.ddd.service.write import create_and_attach_mini_training_service


class TestCreateMiniTrainingAndAttach(TestCase):
    def setUp(self) -> None:
        self.command = command.CreateMiniTrainingAndPasteCommand(
            code="CODE",
            year=2020,
            type="A type",
            abbreviated_title="ABBR",
            title_fr="Title fr",
            title_en="Title en",
            status="",
            schedule_type="",
            credits=25,
            constraint_type="",
            min_constraint=0,
            max_constraint=0,
            management_entity_acronym="MANA",
            teaching_campus_name="CAMP",
            organization_name="ORG",
            remark_fr="remarkr",
            remark_en="en",
            start_year=2020,
            end_year=None,
            path_to_paste="1|15",
            keywords=''
        )

    @mock.patch("program_management.ddd.service.write.paste_element_service.paste_element")
    @mock.patch("program_management.ddd.service.write.create_mini_training_with_program_tree."
                "create_and_report_mini_training_with_program_tree")
    def test_should_call_create_orphan_service_and_paste_element_service_when_called(
            self,
            mock_create_service,
            mock_paste_element):
        mini_training_identity = mini_training.MiniTrainingIdentity(acronym="ACRO", year=2020)
        mock_create_service.return_value = [mini_training_identity]
        resulting_identity = create_and_attach_mini_training_service.create_mini_training_and_paste(self.command)

        self.assertTrue(mock_create_service.called)
        self.assertTrue(mock_paste_element.called)
        self.assertTrue(resulting_identity, mini_training_identity)

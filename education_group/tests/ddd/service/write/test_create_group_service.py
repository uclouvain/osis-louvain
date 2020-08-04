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
from unittest.mock import patch

from django.test import TestCase

from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import GroupType
from education_group.ddd import command
from education_group.ddd.service.write import create_group_service


class TestCreateGroup(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = command.CreateOrphanGroupCommand(
            year=2018,
            code="LTRONC1",
            type=GroupType.COMMON_CORE.name,
            abbreviated_title="Tronc-commun",
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
            start_year=2018,
            end_year=None,
        )

    @patch('education_group.publisher.group_created', autospec=True)
    @patch('education_group.ddd.service.write.create_group_service.GroupRepository.create')
    def test_assert_repository_called_and_signal_dispatched(self, mock_create_repo, mock_publisher):
        create_group_service.create_orphan_group(self.cmd)

        self.assertTrue(mock_create_repo.called)
        # Ensure event is emited
        self.assertTrue(mock_publisher.send.called)

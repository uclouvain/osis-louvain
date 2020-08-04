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
from education_group.ddd import command
from education_group.ddd.domain.group import GroupIdentity
from education_group.ddd.factories.group import GroupFactory
from education_group.ddd.service.write import update_group_service


class TestUpdateGroup(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = command.UpdateGroupCommand(
            year=2018,
            code="LTRONC1",
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
        )

    @patch('education_group.ddd.service.write.update_group_service.GroupRepository', autospec=True)
    def test_assert_repository_called(self, mock_group_repo):
        update_group_service.update_group(self.cmd)

        mock_group_repo.get.return_value = GroupFactory(
            entity_identity=GroupIdentity(code=self.cmd.code, year=self.cmd.year)
        )
        self.assertTrue(mock_group_repo.get.called)
        self.assertTrue(mock_group_repo.update.called)

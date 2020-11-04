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
from education_group.ddd.domain import group
from education_group.ddd.service.write import create_group_service
from education_group.tests.ddd.factories.repository.fake import get_fake_group_repository
from testing.mocks import MockPatcherMixin


class TestCreateGroup(TestCase, MockPatcherMixin):
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

    def setUp(self) -> None:
        self.fake_group_repo = get_fake_group_repository([])
        self.mock_repo("education_group.ddd.repository.group.GroupRepository", self.fake_group_repo)

    def test_should_return_identity_of_group_created(self):
        result = create_group_service.create_orphan_group(self.cmd)

        expected_result = group.GroupIdentity(code=self.cmd.code, year=self.cmd.year)
        self.assertEqual(expected_result, result)

    def test_should_save_created_group_to_repository(self):
        entity_id_of_created_group = create_group_service.create_orphan_group(self.cmd)

        self.assertTrue(self.fake_group_repo.get(entity_id_of_created_group))

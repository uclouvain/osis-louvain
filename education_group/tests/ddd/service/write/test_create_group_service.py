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
import attr

from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import GroupType
from education_group.ddd import command
from education_group.ddd.domain import group
from education_group.ddd.domain.exception import CodeAlreadyExistException, ContentConstraintTypeMissing, \
    ContentConstraintMinimumMaximumMissing, ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum, \
    CreditShouldBeGreaterOrEqualsThanZero, ContentConstraintMaximumInvalid
from education_group.ddd.service.write import create_group_service
from education_group.ddd.validators import _content_constraint, _credits
from education_group.tests.ddd.factories.group import GroupFactory
from testing.testcases import DDDTestCase


class TestCreateGroup(DDDTestCase):
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

    def test_cannot_create_group_with_code_that_is_already_used(self):
        GroupFactory(entity_identity__code=self.cmd.code, persist=True)

        with self.assertRaisesBusinessException(CodeAlreadyExistException):
            create_group_service.create_orphan_group(self.cmd)

    def test_must_define_minimum_or_maximum_constraint_if_constraint_type_is_set(self):
        cmd = attr.evolve(self.cmd, min_constraint=None, max_constraint=None)

        with self.assertRaisesBusinessException(ContentConstraintMinimumMaximumMissing):
            create_group_service.create_orphan_group(cmd)

    def test_must_define_constraint_type_if_minimum_or_maximum_constraint_is_set(self):
        cmd = attr.evolve(self.cmd, constraint_type=None)

        with self.assertRaisesBusinessException(ContentConstraintTypeMissing):
            create_group_service.create_orphan_group(cmd)

    def test_cannot_have_minimum_constraint_greater_than_maximum_constraint_value(self):
        cmd = attr.evolve(self.cmd, min_constraint=11, max_constraint=10)

        with self.assertRaisesBusinessException(ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum):
            create_group_service.create_orphan_group(cmd)

    def test_constraint_values_must_comprised_between_min_and_max_accepted_constraint_values(self):
        cmd = attr.evolve(
            self.cmd,
            min_constraint=_content_constraint.MIN_CONSTRAINT_VALUE - 1,
            max_constraint=_content_constraint.MAX_CONSTRAINT_VALUE + 1
        )
        with self.assertRaisesBusinessException(ContentConstraintMaximumInvalid):
            create_group_service.create_orphan_group(cmd)

    def test_cannot_have_credits_lower_than_min_accepted_credits_value(self):
        cmd = attr.evolve(self.cmd, credits=_credits.MIN_CREDITS_VALUE - 1)

        with self.assertRaisesBusinessException(CreditShouldBeGreaterOrEqualsThanZero):
            create_group_service.create_orphan_group(cmd)

    def test_should_return_identity_of_group_created(self):
        result = create_group_service.create_orphan_group(self.cmd)

        expected_result = group.GroupIdentity(code=self.cmd.code, year=self.cmd.year)
        self.assertEqual(expected_result, result)

    def test_should_save_created_group_to_repository(self):
        entity_id_of_created_group = create_group_service.create_orphan_group(self.cmd)

        self.assertTrue(self.fake_group_repository.get(entity_id_of_created_group))

    def test_should_save_code_with_uppercase(self):
        #  FIXME should be a validation and not a converter
        cmd = attr.evolve(self.cmd, code='LtroNc1')

        identity = create_group_service.create_orphan_group(cmd)

        self.assertEqual(cmd.code.upper(), self.fake_group_repository.get(identity).code)

    def test_should_save_abbreviated_title_with_uppercase(self):
        identity = create_group_service.create_orphan_group(self.cmd)

        self.assertEqual(self.cmd.abbreviated_title.upper(), self.fake_group_repository.get(identity).abbreviated_title)

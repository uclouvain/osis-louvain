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
from education_group.ddd import command
from education_group.ddd.domain import group
from education_group.ddd.domain.exception import ContentConstraintMinimumMaximumMissing, \
    CreditShouldBeGreaterOrEqualsThanZero
from education_group.ddd.service.write import update_group_service
from education_group.ddd.validators import _credits
from education_group.tests.ddd.factories.group import GroupFactory
from testing.testcases import DDDTestCase


class TestUpdateGroup(DDDTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = command.UpdateGroupCommand(
            year=2018,
            code="LTRONC1",
            abbreviated_title="TRONC-COMMUN",
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
            end_year=None,
        )

    def setUp(self) -> None:
        super().setUp()

        self.group_2018, self.group_2019 = GroupFactory.multiple(
            2,
            entity_identity__code=self.cmd.code,
            entity_identity__year=2018,
            persist=True
        )

    def test_must_check_constraints_are_valid(self):
        # For all business rules for constraints see TestCreateGroup test cases
        cmd = attr.evolve(self.cmd, min_constraint=None, max_constraint=None)

        with self.assertRaisesBusinessException(ContentConstraintMinimumMaximumMissing):
            update_group_service.update_group(cmd)

    def test_cannot_have_credits_lower_than_min_accepted_credits_value(self):
        cmd = attr.evolve(self.cmd, credits=_credits.MIN_CREDITS_VALUE - 1)

        with self.assertRaisesBusinessException(CreditShouldBeGreaterOrEqualsThanZero):
            update_group_service.update_group(cmd)

    def test_should_return_entity_id_of_updated_group(self):
        result = update_group_service.update_group(self.cmd)

        expected_result = group.GroupIdentity(code=self.cmd.code, year=self.cmd.year)
        self.assertEqual(expected_result, result)

    def test_should_update_value_of_group_based_on_command_value(self):
        entity_id = update_group_service.update_group(self.cmd)

        group_updated = self.fake_group_repository.get(entity_id)
        self.assert_has_same_value_as_update_command(group_updated)

    def assert_has_same_value_as_update_command(self, update_group: 'group.Group'):
        self.assertEqual(update_group.titles.title_fr, self.cmd.title_fr)
        self.assertEqual(update_group.titles.title_en, self.cmd.title_en)
        self.assertEqual(update_group.credits, self.cmd.credits)
        self.assertEqual(update_group.titles.title_en, self.cmd.title_en)
        self.assertEqual(update_group.content_constraint.type.name, self.cmd.constraint_type)
        self.assertEqual(update_group.content_constraint.maximum, self.cmd.max_constraint)
        self.assertEqual(update_group.content_constraint.minimum, self.cmd.min_constraint)
        self.assertEqual(update_group.management_entity.acronym, self.cmd.management_entity_acronym)
        self.assertEqual(update_group.teaching_campus.name, self.cmd.teaching_campus_name)
        self.assertEqual(update_group.teaching_campus.university_name, self.cmd.organization_name)
        self.assertEqual(update_group.remark.text_fr, self.cmd.remark_fr)
        self.assertEqual(update_group.remark.text_en, self.cmd.remark_en)
        self.assertEqual(update_group.end_year, self.cmd.end_year)
        self.assertEqual(update_group.abbreviated_title, self.cmd.abbreviated_title)

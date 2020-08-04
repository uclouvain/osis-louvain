##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import collections

from django.test import SimpleTestCase

from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import GroupType
from education_group.ddd.command import CreateOrphanGroupCommand
from education_group.ddd.domain import group
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain._remark import Remark
from education_group.ddd.domain._titles import Titles
from education_group.ddd.domain._entity import Entity
from education_group.ddd.domain.group import GroupIdentity, Group
from education_group.ddd.factories.group import GroupFactory


class TestGroupIdentity(SimpleTestCase):
    def test_assert_equals(self):
        group_identity_1 = GroupIdentity(code="LTONC1000", year=2010)
        group_identity_2 = GroupIdentity(code="LTONC1000", year=2010)

        self.assertEqual(group_identity_1, group_identity_2)

    def test_assert_object_is_hashable(self):
        group_identity_1 = GroupIdentity(code="LTONC1000", year=2010)
        self.assertIsInstance(group_identity_1, collections.Hashable)

    def test_assert_code_is_upperized(self):
        group_identity_1 = GroupIdentity(code="ltronc1000", year=2010)
        self.assertEqual(group_identity_1.code, "LTRONC1000")


class TestGroup(SimpleTestCase):
    def setUp(self):
        self.group = GroupFactory()

    def test_assert_code_property(self):
        self.assertEqual(
            self.group.code,
            self.group.entity_id.code
        )

    def test_assert_year_property(self):
        self.assertEqual(
            self.group.year,
            self.group.entity_id.year
        )

    def test_assert_abbreviated_title_is_upperized(self):
        group = Group(
            entity_identity=GroupIdentity(code="LTONC1000", year=2010),
            type=GroupType.COMMON_CORE,
            abbreviated_title='titletobeupper',
            titles=Titles(title_fr='', title_en=''),
            credits=5,
            content_constraint=ContentConstraint(type=ConstraintTypeEnum.CREDITS, minimum=0, maximum=15),
            management_entity=Entity(acronym="DRT"),
            teaching_campus=Campus(name="Fucam Mons", university_name="UCLouvain"),
            remark=Remark(text_fr='', text_en=''),
            start_year=2010
        )
        self.assertEqual(group.abbreviated_title, "TITLETOBEUPPER")

    def test_assert_is_minor_major_option_list_choice(self):
        group_types = [GroupType.MINOR_LIST_CHOICE, GroupType.OPTION_LIST_CHOICE, GroupType.MAJOR_LIST_CHOICE]
        for group_type in group_types:
            with self.subTest(group_type=group_type):
                self.group.type = group_type
                self.assertTrue(self.group.is_minor_major_option_list_choice())


class TestGroupBuilder(SimpleTestCase):
    def setUp(self):
        self.cmd = CreateOrphanGroupCommand(
            code="LTRONC100T",
            year=2018,
            type=GroupType.COMMON_CORE.name,
            abbreviated_title="Intitulé en francais",
            title_fr="Titre en français",
            title_en="Title in english",
            credits=30,
            constraint_type=ConstraintTypeEnum.CREDITS.name,
            min_constraint=0,
            max_constraint=20,
            management_entity_acronym="AGRO",
            teaching_campus_name="Mons Fucam",
            organization_name="UCLouvain",
            remark_fr="Remarque en francais",
            remark_en="Remark in english",
            start_year=2018,
            end_year=None,
        )

    def test_assert_return_instance(self):
        self.assertIsInstance(
            group.builder.build_from_create_cmd(self.cmd),
            Group
        )

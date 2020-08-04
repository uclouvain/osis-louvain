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
from typing import List

from django.test import TestCase

from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import GroupType, TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_type import GroupEducationGroupTypeFactory
from base.tests.factories.entity_version import EntityVersionFactory
from education_group.ddd.domain import exception
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain._remark import Remark
from education_group.ddd.domain._titles import Titles
from education_group.ddd.domain._entity import Entity as EntityValueObject
from education_group.ddd.domain.exception import AcademicYearNotFound, TypeNotFound, ManagementEntityNotFound, \
    TeachingCampusNotFound, GroupCodeAlreadyExistException
from education_group.ddd.domain.group import GroupIdentity, Group
from education_group.ddd.factories.group import GroupFactory
from education_group.ddd.repository.group import GroupRepository
from education_group.tests.factories.group_year import GroupYearFactory
from education_group.tests.factories.group import GroupFactory as GroupModelDbFactory
from education_group.models.group_year import GroupYear as GroupYearModelDb


class TestGroupRepositoryGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.management_entity_version = EntityVersionFactory(acronym='DRT')
        cls.group_year_db = GroupYearFactory(
            management_entity_id=cls.management_entity_version.entity_id,
            education_group_type=GroupEducationGroupTypeFactory()
        )
        cls.group_identity = GroupIdentity(
            code=cls.group_year_db.partial_acronym,
            year=cls.group_year_db.academic_year.year,
        )

    def test_case_group_not_exists(self):
        dummy_group_identity = GroupIdentity(
            code="dummy-code",
            year=1966,
        )
        with self.assertRaises(exception.GroupNotFoundException):
            GroupRepository.get(dummy_group_identity)

    def test_fields_mapping(self):
        group = GroupRepository.get(self.group_identity)
        self.assertIsInstance(group, Group)

        self.assertEqual(group.entity_id, self.group_identity)
        self.assertEqual(group.type, GroupType[self.group_year_db.education_group_type.name])
        self.assertEqual(group.abbreviated_title, self.group_year_db.acronym)
        self.assertEqual(group.credits, self.group_year_db.credits)
        self.assertEqual(group.start_year, self.group_year_db.group.start_year.year)
        self.assertIsNone(group.end_year)

        self.assertIsInstance(group.titles, Titles)
        self.assertEqual(
            group.titles,
            Titles(title_fr=self.group_year_db.title_fr, title_en=self.group_year_db.title_en)
        )

        self.assertIsInstance(group.content_constraint, ContentConstraint)
        self.assertEqual(
            group.content_constraint,
            ContentConstraint(
                type=ConstraintTypeEnum[self.group_year_db.constraint_type],
                minimum=self.group_year_db.min_constraint,
                maximum=self.group_year_db.max_constraint
            )
        )

        self.assertIsInstance(group.management_entity, EntityValueObject)
        self.assertEqual(
            group.management_entity,
            EntityValueObject(
                acronym=self.management_entity_version.acronym,
            )
        )

        self.assertIsInstance(group.teaching_campus, Campus)
        self.assertEqual(
            group.teaching_campus,
            Campus(
                name=self.group_year_db.main_teaching_campus.name,
                university_name=self.group_year_db.main_teaching_campus.organization.name,
            )
        )

        self.assertIsInstance(group.remark, Remark)
        self.assertEqual(
            group.remark,
            Remark(
                text_fr=self.group_year_db.remark_fr,
                text_en=self.group_year_db.remark_en
            )
        )


class TestGroupRepositoryCreateMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create database data
        cls.management_entity_version = EntityVersionFactory(acronym='DRT')
        cls.education_group_type = GroupEducationGroupTypeFactory()
        cls.academic_year = AcademicYearFactory(year=2017)
        cls.campus = CampusFactory()

    def setUp(self):
        # Construct DDD model based on database data
        self.group_identity = GroupIdentity(code="LTRONC1200", year=2017)
        self.group = GroupFactory(
            entity_identity=self.group_identity,
            type=self.education_group_type,
            management_entity=EntityValueObject(acronym='DRT'),
            teaching_campus=Campus(
                name=self.campus.name,
                university_name=self.campus.organization.name,
            ),
            start_year=2017,
            end_year=None
        )

    def test_assert_raise_academic_year_not_found(self):
        self.group.entity_id.year = 2000
        with self.assertRaises(AcademicYearNotFound):
            GroupRepository.create(self.group)

    def test_assert_raise_group_type_not_found(self):
        self.group.type = TrainingType.BACHELOR
        with self.assertRaises(TypeNotFound):
            GroupRepository.create(self.group)

    def test_assert_raise_management_entity_not_found(self):
        self.group.management_entity = EntityValueObject(acronym='AGRO')
        with self.assertRaises(ManagementEntityNotFound):
            GroupRepository.create(self.group)

    def test_assert_raise_teaching_campus_not_found(self):
        self.group.teaching_campus = Campus(
            name="Fucam Mons",
            university_name="UCLouvain",
        )
        with self.assertRaises(TeachingCampusNotFound):
            GroupRepository.create(self.group)

    def test_assert_group_created_map_fields(self):
        group_identity = GroupRepository.create(self.group)

        self.assertIsInstance(group_identity, GroupIdentity)
        self.assertEqual(group_identity, self.group_identity)

        group_inserted = GroupYearModelDb.objects.get(
            partial_acronym=group_identity.code,
            academic_year__year=group_identity.year
        )
        self.assertEqual(group_inserted.acronym, self.group.abbreviated_title)
        self.assertEqual(group_inserted.title_fr, self.group.titles.title_fr)
        self.assertEqual(group_inserted.title_en, self.group.titles.title_en)
        self.assertEqual(group_inserted.constraint_type, self.group.content_constraint.type.name)
        self.assertEqual(group_inserted.min_constraint, self.group.content_constraint.minimum)
        self.assertEqual(group_inserted.max_constraint, self.group.content_constraint.maximum)

        self.assertEqual(group_inserted.remark_en, self.group.remark.text_en)
        self.assertEqual(group_inserted.remark_fr, self.group.remark.text_fr)

        self.assertEqual(group_inserted.management_entity_id, self.management_entity_version.entity_id)
        self.assertEqual(group_inserted.academic_year_id, self.academic_year.pk)
        self.assertEqual(group_inserted.education_group_type_id, self.education_group_type.pk)
        self.assertEqual(group_inserted.main_teaching_campus_id, self.campus.pk)

    def test_assert_unannualized_identity_correctly_save(self):
        group_identity = GroupRepository.create(self.group)

        group_inserted = GroupYearModelDb.objects.get(
            partial_acronym=group_identity.code,
            academic_year__year=group_identity.year
        )
        self.assertEqual(group_inserted.group.start_year.year, 2017)
        self.assertIsNone(group_inserted.group.end_year)

    def test_assert_raise_group_code_already_exist_exception(self):
        GroupRepository.create(self.group)
        with self.assertRaises(GroupCodeAlreadyExistException):
            GroupRepository.create(self.group)


class TestGroupRepositorySearchMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.management_entity_version = EntityVersionFactory(acronym='DRT')
        cls.group_year_db = GroupYearFactory(
            management_entity_id=cls.management_entity_version.entity_id,
            education_group_type=GroupEducationGroupTypeFactory()
        )
        cls.group_identity = GroupIdentity(
            code=cls.group_year_db.partial_acronym,
            year=cls.group_year_db.academic_year.year,
        )

        cls.group_year_db_2 = GroupYearFactory(
            management_entity_id=cls.management_entity_version.entity_id,
            education_group_type=GroupEducationGroupTypeFactory()
        )
        cls.group_identity_2 = GroupIdentity(
            code=cls.group_year_db_2.partial_acronym,
            year=cls.group_year_db_2.academic_year.year,
        )

    def test_assert_search_case_empty_list(self):
        self.assertListEqual(
            GroupRepository.search([]),
            []
        )

    def test_assert_search_one_entity_id(self):
        results = GroupRepository.search([self.group_identity])

        self.assertIsInstance(results, List)
        self.assertEqual(len(results), 1, msg="Should have one result because search only on one ID")
        self.assertIsInstance(results[0], Group)
        self.assertEqual(
            results[0].entity_id,
            self.group_identity
        )

    def test_assert_search_multiple_entity_id(self):
        results = GroupRepository.search([self.group_identity, self.group_identity_2])

        self.assertIsInstance(results, List)
        self.assertEqual(len(results), 2, msg="Should have two results because search on multiple ID")
        self.assertIsInstance(results[0], Group)


class TestGroupRepositoryUpdateMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.management_entity_version = EntityVersionFactory(acronym='DRT')
        cls.education_group_type = GroupEducationGroupTypeFactory()

    def setUp(self) -> None:
        self.group_year_db = GroupYearFactory(
            management_entity_id=self.management_entity_version.entity_id,
            education_group_type=self.education_group_type
        )
        self.group_identity = GroupIdentity(
            code=self.group_year_db.partial_acronym,
            year=self.group_year_db.academic_year.year,
        )

    def test_case_group_not_exists(self):
        dummy_group_identity = GroupIdentity(code="dummy-code", year=1966)
        group = GroupFactory(
            entity_identity=dummy_group_identity,
            management_entity=EntityValueObject(acronym='DRT'),
            teaching_campus=Campus(
                name=self.group_year_db.main_teaching_campus.name,
                university_name=self.group_year_db.main_teaching_campus.organization.name,
            )
        )
        with self.assertRaises(exception.GroupNotFoundException):
            GroupRepository.update(group)

    def test_assert_update_modify_field(self):
        new_entity = EntityVersionFactory(acronym='AGRO')

        group = GroupFactory(
            entity_identity=self.group_identity,
            management_entity=EntityValueObject(acronym=new_entity.acronym),
            teaching_campus=Campus(
                name=self.group_year_db.main_teaching_campus.name,
                university_name=self.group_year_db.main_teaching_campus.organization.name,
            )
        )
        GroupRepository.update(group)

        self.group_year_db.refresh_from_db()
        self.assertEqual(group.abbreviated_title, self.group_year_db.acronym)
        self.assertEqual(group.titles.title_fr, self.group_year_db.title_fr)
        self.assertEqual(group.titles.title_en, self.group_year_db.title_en)
        self.assertEqual(group.credits, self.group_year_db.credits)
        self.assertEqual(group.management_entity.acronym, 'AGRO')
        self.assertEqual(group.content_constraint.type.name, self.group_year_db.constraint_type)
        self.assertEqual(group.content_constraint.minimum, self.group_year_db.min_constraint)
        self.assertEqual(group.content_constraint.maximum, self.group_year_db.max_constraint)
        self.assertEqual(group.remark.text_fr, self.group_year_db.remark_fr)
        self.assertEqual(group.remark.text_en, self.group_year_db.remark_en)


class TestGroupRepositoryDeleteMethod(TestCase):
    def setUp(self) -> None:
        self.group_year_db = GroupYearFactory()

    def test_assert_delete_in_database(self):
        group_id = GroupIdentity(code=self.group_year_db.partial_acronym, year=self.group_year_db.academic_year.year)
        GroupRepository.delete(group_id)

        with self.assertRaises(GroupYearModelDb.DoesNotExist):
            GroupYearModelDb.objects.get(partial_acronym=group_id.code, academic_year__year=group_id.year)

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
from django.forms import model_to_dict
from django.test import TestCase

from base.models import education_group_year
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_types
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import MiniTrainingEducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from education_group.ddd.domain import exception
from education_group.ddd.domain._entity import Entity as EntityValueObject
from education_group.ddd.domain.mini_training import MiniTrainingIdentity, MiniTraining
from education_group.ddd.repository import mini_training
from education_group.tests.factories.mini_training import MiniTrainingFactory


class TestMiniTrainingRepositoryCreateMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_foreign_key_database_data()
        cls.mini_training = MiniTrainingFactory(
            entity_identity=MiniTrainingIdentity(acronym="LOIS58", year=cls.academic_year.year),
            start_year=cls.academic_year.year,
            type=education_group_types.MiniTrainingType[cls.education_group_type.name],
            management_entity=EntityValueObject(acronym='DRT'),
        )

    @classmethod
    def _create_foreign_key_database_data(cls):
        cls.academic_year = AcademicYearFactory()
        cls.management_entity_version = EntityVersionFactory(acronym='DRT')
        cls.education_group_type = MiniTrainingEducationGroupTypeFactory()

    def test_should_create_db_data_with_correct_values_taken_from_domain_object(self):
        mini_training_identity = mini_training.MiniTrainingRepository.create(self.mini_training)

        education_group_year_db_obj = education_group_year.EducationGroupYear.objects.get(
            acronym=mini_training_identity.acronym,
            academic_year__year=mini_training_identity.year
        )
        self.assert_education_group_year_equal_to_domain(education_group_year_db_obj, self.mini_training)

    def assert_education_group_year_equal_to_domain(
            self,
            db_education_group_year: education_group_year.EducationGroupYear,
            domain_obj: MiniTraining):
        expected_values = {
            "academic_year": self.academic_year.id,
            "partial_acronym": domain_obj.code,
            "education_group_type": self.education_group_type.id,
            "acronym": domain_obj.acronym,
            "title": domain_obj.titles.title_fr,
            "title_english": domain_obj.titles.title_en,
            "credits": domain_obj.credits,
            "management_entity": self.management_entity_version.entity.id,
        }

        actual_values = model_to_dict(
            db_education_group_year,
            fields=(
                "academic_year", "partial_acronym", "education_group_type", "acronym", "title", "title_english",
                "credits", "management_entity",
            )
        )
        self.assertDictEqual(expected_values, actual_values)


class TestMiniTrainingRepositoryGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year_db = EducationGroupYearFactory(education_group_type__minitraining=True)

    def test_should_raise_mini_training_not_found_exception_when_matching_mini_training_does_not_exist(self):
        inexistent_mini_training_identity = MiniTrainingIdentity(acronym="INEXISTENT", year=2025)
        with self.assertRaises(exception.MiniTrainingNotFoundException):
            mini_training.MiniTrainingRepository.get(inexistent_mini_training_identity)

    def test_should_return_domain_object_when_matching_mini_training_found(self):
        existing_mini_training_identity = MiniTrainingIdentity(
            acronym=self.education_group_year_db.acronym,
            year=self.education_group_year_db.academic_year.year
        )
        result = mini_training.MiniTrainingRepository.get(existing_mini_training_identity)
        self.assertEqual(
            result.entity_id,
            existing_mini_training_identity
        )


class TestMiniTrainingRepositoryUpdateMethod(TestCase):
    def setUp(self) -> None:
        self.education_group_year_db = EducationGroupYearFactory(
            partial_acronym="CODE",
            acronym="ACRONYM",
            academic_year__year=2022,
            education_group_type__minitraining=True
        )
        self.management_entity = EntityVersionFactory(acronym="MANA")

        self.mini_training_to_persist_update = MiniTrainingFactory(
            entity_identity__acronym=self.education_group_year_db.acronym,
            entity_identity__year=self.education_group_year_db.academic_year.year,
            type=education_group_types.MiniTrainingType[self.education_group_year_db.education_group_type.name],
            management_entity__acronym="MANA",
        )

    def test_should_raise_mini_training_not_found_exception_when_mini_training_not_existing_in_repository(self):
        inexistent_mini_training = MiniTrainingFactory(entity_identity__acronym="INEXISTENT")

        with self.assertRaises(exception.MiniTrainingNotFoundException):
            mini_training.MiniTrainingRepository.update(inexistent_mini_training)

    def test_should_return_entity_identity(self):
        result = mini_training.MiniTrainingRepository.update(self.mini_training_to_persist_update)

        self.assertEqual(self.mini_training_to_persist_update.entity_id, result)

    def test_should_persist_fields(self):
        mini_training.MiniTrainingRepository.update(self.mini_training_to_persist_update)

        self.education_group_year_db.refresh_from_db()

        self._assert_fields_updated_to_repository(
            self.mini_training_to_persist_update,
            self.education_group_year_db
        )

    def _assert_fields_updated_to_repository(self, domain_obj: 'MiniTraining', repo_obj: 'EducationGroupYear'):
        self.assertEqual(domain_obj.end_year, repo_obj.education_group.end_year)

        self.assertEqual(domain_obj.titles.title_fr, repo_obj.title)
        self.assertEqual(domain_obj.titles.title_en, repo_obj.title_english)

        self.assertEqual(domain_obj.status.name, repo_obj.active)
        self.assertEqual(domain_obj.schedule_type.name, repo_obj.schedule_type)
        self.assertEqual(domain_obj.credits, repo_obj.credits)
        self.assertEqual(domain_obj.keywords, repo_obj.keywords)

        self.assertEqual(domain_obj.management_entity.acronym, repo_obj.management_entity_version.acronym)


class TestMiniTrainingDeleteMethod(TestCase):
    def setUp(self) -> None:
        self.education_group_year_db = EducationGroupYearFactory(education_group_type__minitraining=True)
        self.entity_identity = MiniTrainingIdentity(
            acronym=self.education_group_year_db.acronym,
            year=self.education_group_year_db.academic_year.year
        )

    def test_should_delete_education_group_year(self):
        mini_training.MiniTrainingRepository.delete(self.entity_identity)

        with self.assertRaises(exception.MiniTrainingNotFoundException):
            mini_training.MiniTrainingRepository.get(self.entity_identity)

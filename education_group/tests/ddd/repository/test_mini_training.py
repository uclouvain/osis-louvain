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
from base.models.enums import education_group_types
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_type import MiniTrainingEducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from education_group.ddd.domain import exception
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._entity import Entity as EntityValueObject
from education_group.ddd.domain.mini_training import MiniTrainingIdentity, MiniTraining
from education_group.ddd.repository import mini_training
from education_group.models import group_year, group
from education_group.tests.factories.mini_training import MiniTrainingFactory
from program_management.models import education_group_version
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory


class TestMiniTrainingRepositoryCreateMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_foreign_key_database_data()
        cls.mini_training = MiniTrainingFactory(
            entity_identity=MiniTrainingIdentity(acronym="LOIS58", year=cls.academic_year.year),
            start_year=cls.academic_year.year,
            type=education_group_types.MiniTrainingType[cls.education_group_type.name],
            management_entity=EntityValueObject(acronym='DRT'),
            teaching_campus=Campus(
                name=cls.campus.name,
                university_name=cls.campus.organization.name,
            ),
        )

    @classmethod
    def _create_foreign_key_database_data(cls):
        cls.academic_year = AcademicYearFactory()
        cls.management_entity_version = EntityVersionFactory(acronym='DRT')
        cls.education_group_type = MiniTrainingEducationGroupTypeFactory()
        cls.campus = CampusFactory()

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
            "main_teaching_campus": self.campus.id,
        }

        actual_values = model_to_dict(
            db_education_group_year,
            fields=(
                "academic_year", "partial_acronym", "education_group_type", "acronym", "title", "title_english",
                "credits", "management_entity",
                "main_teaching_campus"
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



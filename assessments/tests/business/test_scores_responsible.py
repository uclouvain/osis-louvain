#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.test import TestCase

from assessments.business import scores_responsible
from base.models.enums import entity_type
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.entity_version import MainEntityVersionFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory


class TestFilterLearningUnitYearAccordingPerson(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.structure = SimpleStructure(cls.current_academic_year)
        cls.learning_unit_years = [
            LearningUnitYearFactory(learning_container_year__requirement_entity=cls.structure.child_1.entity),
            LearningUnitYearFactory(learning_container_year__requirement_entity=cls.structure.child_1_1.entity),
            LearningUnitYearFactory(learning_container_year__requirement_entity=cls.structure.child_1_2.entity),
            LearningUnitYearFactory(learning_container_year__requirement_entity=cls.structure.child_3.entity)
        ]

        cls.program_sector = EducationGroupYearFactory(
            administration_entity=cls.structure.child_2.entity,
            academic_year=cls.current_academic_year
        )
        cls.program_faculty = EducationGroupYearFactory(
            administration_entity=cls.structure.child_2_1.entity,
            academic_year=cls.current_academic_year
        )
        cls.program_school = EducationGroupYearFactory(
            administration_entity=cls.structure.child_2_1_1.entity,
            academic_year=cls.current_academic_year
        )
        cls.program_inactive = EducationGroupYearFactory(
            administration_entity=cls.structure.child_3.entity,
            academic_year=cls.current_academic_year
        )

        cls.learning_unit_enrollments = [
            LearningUnitEnrollmentFactory(
                learning_unit_year__learning_container_year__requirement_entity=cls.structure.child_2_1.entity,
                offer_enrollment__education_group_year=cls.program_sector
            ),
            LearningUnitEnrollmentFactory(
                learning_unit_year__learning_container_year__requirement_entity=cls.structure.child_1.entity,
                offer_enrollment__education_group_year=cls.program_sector
            ),
            LearningUnitEnrollmentFactory(
                learning_unit_year__learning_container_year__requirement_entity=cls.structure.child_2_1.entity,
                offer_enrollment__education_group_year=cls.program_faculty
            ),
            LearningUnitEnrollmentFactory(
                learning_unit_year__learning_container_year__requirement_entity=cls.structure.child_2_1_1.entity,
                offer_enrollment__education_group_year=cls.program_faculty
            ),
            LearningUnitEnrollmentFactory(
                learning_unit_year__learning_container_year__requirement_entity=cls.structure.child_2_1_1.entity,
                offer_enrollment__education_group_year=cls.program_school
            ),
            LearningUnitEnrollmentFactory(
                learning_unit_year__learning_container_year__requirement_entity=cls.structure.child_3.entity,
                offer_enrollment__education_group_year=cls.program_inactive
            ),
        ]

    def test_should_return_empty_list_if_person_is_not_linked_to_any_entities(self):
        person = PersonFactory()
        result = scores_responsible.filter_learning_unit_year_according_person(
            LearningUnitYear.objects.all(),
            person
        )

        self.assertQuerysetEqual(result, LearningUnitYear.objects.none())

    def test_if_entity_manager_with_entity_not_linked_to_any_learning_unit_year_should_return_empty_qs(self):
        manager = EntityManagerFactory()

        result = scores_responsible.filter_learning_unit_year_according_person(
            LearningUnitYear.objects.all(),
            manager.person
        )

        self.assertQuerysetEqual(
            result,
            LearningUnitYear.objects.none(),
            transform=lambda obj: obj,
            ordered=False
        )

    def test_if_entity_manager_should_return_learning_unit_years_link_to_entity(self):
        manager = EntityManagerFactory(entity=self.structure.child_1.entity, with_child=False)

        result = scores_responsible.filter_learning_unit_year_according_person(
            LearningUnitYear.objects.all(),
            manager.person
        )

        self.assertQuerysetEqual(
            result,
            LearningUnitYear.objects.filter(learning_container_year__requirement_entity=self.structure.child_1.entity),
            transform=lambda obj: obj,
            ordered=False
        )

    def test_if_entity_manager_with_child_should_return_learning_unit_years_link_to_entity_and_child_entities(self):
        manager = EntityManagerFactory(entity=self.structure.child_1.entity, with_child=True)

        result = scores_responsible.filter_learning_unit_year_according_person(
            LearningUnitYear.objects.all(),
            manager.person
        )

        entities = [self.structure.child_1.entity, self.structure.child_1_1.entity, self.structure.child_1_2.entity]
        self.assertQuerysetEqual(
            result,
            LearningUnitYear.objects.filter(learning_container_year__requirement_entity__in=entities),
            transform=lambda obj: obj,
            ordered=False
        )

    def test_if_entity_manager_of_inactive_entity_should_return_the_learning_unit_years_linked_to_inactive_entity(self):
        manager = EntityManagerFactory(entity=self.structure.child_3.entity, with_child=True)

        result = scores_responsible.filter_learning_unit_year_according_person(
            LearningUnitYear.objects.all(),
            manager.person
        )

        entities = [self.structure.child_3.entity]
        self.assertQuerysetEqual(
            result,
            LearningUnitYear.objects.filter(learning_container_year__requirement_entity__in=entities),
            transform=lambda obj: obj,
            ordered=False
        )

    def test_if_program_manager_and_no_learning_unit_year_in_the_programs_in_charge_should_return_empty_list(self):
        manager = ProgramManagerFactory()
        result = scores_responsible.filter_learning_unit_year_according_person(
            LearningUnitYear.objects.all(),
            manager.person
        )

        self.assertQuerysetEqual(
            result,
            LearningUnitYear.objects.none(),
            transform=lambda obj: obj,
            ordered=False
        )

    def test_if_program_manager_should_return_luy_having_requirement_entity_inside_program_administrative_entity(self):
        manager = ProgramManagerFactory(education_group=self.program_sector.education_group)
        result = scores_responsible.filter_learning_unit_year_according_person(
            LearningUnitYear.objects.all(),
            manager.person
        )

        entities = [self.structure.child_2.entity, self.structure.child_2_1.entity, self.structure.child_2_1_1.entity]
        self.assertQuerysetEqual(
            result,
            LearningUnitYear.objects.filter(
                learning_container_year__requirement_entity__in=entities,
                learningunitenrollment__offer_enrollment__education_group_year__education_group=manager.education_group
            ),
            transform=lambda obj: obj,
            ordered=False
        )

    def test_if_program_manager_and_administrative_in_faculty_should_return_luy_having_same_faculty_as_program(self):
        manager = ProgramManagerFactory(education_group=self.program_school.education_group)
        result = scores_responsible.filter_learning_unit_year_according_person(
            LearningUnitYear.objects.all(),
            manager.person
        )

        entities = [self.structure.child_2_1.entity, self.structure.child_2_1_1.entity]
        self.assertQuerysetEqual(
            result,
            LearningUnitYear.objects.filter(
                learning_container_year__requirement_entity__in=entities,
                learningunitenrollment__offer_enrollment__education_group_year__education_group=manager.education_group
            ),
            transform=lambda obj: obj,
            ordered=False
        )

    def test_if_program_manager_should_take_into_account_for_inactive_entity(self):
        manager = ProgramManagerFactory(education_group=self.program_inactive.education_group)
        result = scores_responsible.filter_learning_unit_year_according_person(
            LearningUnitYear.objects.all(),
            manager.person
        )

        entities = [self.structure.child_3.entity]
        self.assertQuerysetEqual(
            result,
            LearningUnitYear.objects.filter(
                learning_container_year__requirement_entity__in=entities,
                learningunitenrollment__offer_enrollment__education_group_year__education_group=manager.education_group
            ),
            transform=lambda obj: obj,
            ordered=False
        )

    def test_should_return_an_union_of_all_the_result_by_role(self):
        person = PersonFactory()
        pgm_manager = ProgramManagerFactory(person=person, education_group=self.program_school.education_group)
        EntityManagerFactory(person=person, entity=self.structure.child_1.entity, with_child=False)

        result = scores_responsible.filter_learning_unit_year_according_person(
            LearningUnitYear.objects.all(),
            person
        )

        entity_entities = [self.structure.child_1.entity]
        entities = [self.structure.child_2_1.entity, self.structure.child_2_1_1.entity]

        expected_qs = LearningUnitYear.objects.filter(
            learning_container_year__requirement_entity__in=entity_entities
        ).union(
            LearningUnitYear.objects.filter(
                learning_container_year__requirement_entity__in=entities,
                learningunitenrollment__offer_enrollment__education_group_year__education_group=
                pgm_manager.education_group
            )
        )
        self.assertQuerysetEqual(
            result,
            expected_qs,
            transform=lambda obj: obj,
            ordered=False
        )


class SimpleStructure:
    def __init__(self, academic_year):
        self.root = MainEntityVersionFactory(title='Root', acronym='UCL', entity_type='', parent=None)

        self.child_1 = MainEntityVersionFactory(
            title='Child 1',
            acronym='SSO',
            entity_type=entity_type.SECTOR,
            parent=self.root.entity
        )
        self.child_1_1 = MainEntityVersionFactory(
            title='Child 1 1',
            acronym='LSO',
            entity_type=entity_type.FACULTY,
            parent=self.child_1.entity
        )
        self.child_1_2 = MainEntityVersionFactory(
            title='Child 1 2',
            acronym='MPA',
            entity_type=entity_type.FACULTY,
            parent=self.child_1.entity
        )

        self.child_2 = MainEntityVersionFactory(
            title='Child 2',
            acronym='SSM',
            entity_type=entity_type.SECTOR,
            parent=self.root.entity
        )
        self.child_2_1 = MainEntityVersionFactory(
            title='Child 2 1',
            acronym='TTR',
            entity_type=entity_type.FACULTY,
            parent=self.child_2.entity
        )
        self.child_2_1_1 = MainEntityVersionFactory(
            title='Child 2 1 1',
            acronym='MPP',
            entity_type=entity_type.SCHOOL,
            parent=self.child_2_1.entity
        )

        self.child_3 = MainEntityVersionFactory(
            title='Inactive',
            acronym='INA',
            entity_type=entity_type.SECTOR,
            parent=self.root.entity,
            end_date=academic_year.start_date - datetime.timedelta(days=10)
        )

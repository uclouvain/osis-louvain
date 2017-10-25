##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase
from django.utils import timezone

from base.business.learning_unit_year_with_context import is_service_course
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.models.enums import entity_container_year_link_type
from reference.tests.factories.country import CountryFactory
from base.forms.learning_units import LearningUnitYearForm

ACRONYM_LU = "LDROI1001"


class TestLearningUnitForm(TestCase):
    def setUp(self):
        self.country = CountryFactory()
        self.academic_yr = AcademicYearFactory(year=timezone.now().year)
        self.start_date = self.academic_yr.start_date
        self.end_date = self.academic_yr.end_date

        l_container = LearningContainerFactory()
        self.l_container_year = LearningContainerYearFactory(acronym=ACRONYM_LU,
                                                             learning_container=l_container,
                                                             academic_year=self.academic_yr)
        LearningUnitYearFactory(acronym=ACRONYM_LU,
                                learning_container_year= self.l_container_year,
                                academic_year=self.academic_yr,
                                learning_unit=LearningUnitFactory())

    def test_is_service_course(self):

        self.build_faculty_entity_tree()

        self.build_allocation_entity_not_in_fac_tree()
        form = LearningUnitYearForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid())
        found_learning_units = form.get_activity_learning_units()
        learning_unit = found_learning_units[0]
        requirement_entity_version = learning_unit.entities.get(entity_container_year_link_type.REQUIREMENT_ENTITY)
        learning_container_year = learning_unit.learning_container_year
        entity_parent = requirement_entity_version.find_parent_faculty_version(learning_container_year.academic_year)

        self.assertTrue(is_service_course(learning_unit.academic_year, requirement_entity_version, learning_container_year, entity_parent))

    def test_is_not_service_course(self):

        self.build_allocation_entity_in_fac_tree()

        form = LearningUnitYearForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid())
        found_learning_units = form.get_activity_learning_units()
        learning_unit = found_learning_units[0]
        requirement_entity_version = learning_unit.entities.get(entity_container_year_link_type.REQUIREMENT_ENTITY)
        learning_container_year = learning_unit.learning_container_year
        entity_parent = requirement_entity_version.find_parent_faculty_version(learning_container_year.academic_year)

        self.assertFalse(is_service_course(learning_unit.academic_year, requirement_entity_version, learning_container_year, entity_parent))

    def build_allocation_entity_not_in_fac_tree(self):
        entity_allocation = EntityFactory()
        EntityVersionFactory(entity=entity_allocation,
                             parent=None,
                             acronym="Entity_allo",
                             start_date=self.start_date,
                             end_date=self.end_date)
        EntityContainerYearFactory(
            entity=entity_allocation,
            learning_container_year=self.l_container_year,
            type=entity_container_year_link_type.ALLOCATION_ENTITY
        )

    def build_faculty_entity_tree(self):
        entity_faculty = EntityFactory(country=self.country)
        EntityVersionFactory(
            entity=entity_faculty,
            acronym="ENTITY_FACULTY",
            title="This is the entity faculty ",
            entity_type="FACULTY",
            parent=None,
            start_date=self.start_date,
            end_date=self.end_date
        )
        entity_school_child_level1 = EntityFactory(country=self.country)
        EntityVersionFactory(entity=entity_school_child_level1,
                             acronym="ENTITY_LEVEL1",
                             title="This is the entity version level1 ",
                             entity_type="SCHOOL",
                             parent=entity_faculty,
                             start_date=self.start_date,
                             end_date=self.end_date)
        entity_school_child_level2 = EntityFactory(country=self.country)
        EntityVersionFactory(
            entity=entity_school_child_level2,
            acronym="ENTITY_LEVEL2",
            title="This is the entity version level 2",
            entity_type="SCHOOL",
            parent=entity_school_child_level1,
            start_date=self.start_date,
            end_date=self.end_date
        )
        entity_requirement = EntityFactory()
        EntityVersionFactory(entity=entity_requirement,
                             parent=entity_school_child_level2,
                             acronym="Entity requi",
                             start_date=self.start_date,
                             end_date=self.end_date)
        EntityContainerYearFactory(
            entity=entity_requirement,
            learning_container_year=self.l_container_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY
        )
        return entity_school_child_level2

    def get_valid_data(self):
        return {
            "academic_year_id": self.academic_yr.pk,
            "acronym": ACRONYM_LU
        }

    def build_allocation_entity_in_fac_tree(self):
        entity_school_child_level2 = self.build_faculty_entity_tree()
        entity_allocation = EntityFactory()
        EntityVersionFactory(entity=entity_allocation,
                             parent=entity_school_child_level2,
                             acronym="Entity_allo",
                             start_date=self.start_date,
                             end_date=self.end_date)
        EntityContainerYearFactory(
            entity=entity_allocation,
            learning_container_year=self.l_container_year,
            type=entity_container_year_link_type.ALLOCATION_ENTITY
        )

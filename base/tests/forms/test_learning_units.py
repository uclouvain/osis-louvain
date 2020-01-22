##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

import base.forms.learning_unit.search.service_course
import base.forms.learning_unit.search.simple
from attribution.tests.factories.attribution import AttributionNewFactory
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from base.business.learning_unit_year_with_context import is_service_course
from base.models.entity_version import PEDAGOGICAL_ENTITY_ADDED_EXCEPTIONS
from base.models.enums import entity_type
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.tutor import TutorFactory
from reference.tests.factories.country import CountryFactory


class TestLearningUnitForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.country = CountryFactory()
        cls.current_ac_year = create_current_academic_year()
        cls.tutor = TutorFactory()
        cls.attribution = AttributionNewFactory(tutor=cls.tutor)
        cls.list_learning_unit_container_year = [
            LearningContainerYearFactory(
                acronym="LC%d" % container,
                academic_year=cls.current_ac_year
            )
            for container in range(4)
        ]
        cls.list_learning_unit_year = cls._create_list_learning_units_from_containers(
            cls.list_learning_unit_container_year,
            cls.current_ac_year
        )
        cls.learning_component = LearningComponentYearFactory(learning_unit_year=cls.list_learning_unit_year[0])
        cls.attribution_charge_new = AttributionChargeNewFactory(
            attribution=cls.attribution,
            learning_component_year=cls.learning_component
        )
        cls.list_entity_version = cls._create_list_entities_version(
            cls.current_ac_year.end_date,
            cls.current_ac_year.start_date
        )

        cls._add_entities_to_containers(
            cls.list_entity_version,
            cls.list_learning_unit_container_year
        )

    @staticmethod
    def _create_list_containers(number_of_containers, ac):
        list_lu_container_year = [
            LearningContainerYearFactory(acronym="LC%d" % container, academic_year=ac)
            for container in range(number_of_containers)
        ]
        return list_lu_container_year

    @staticmethod
    def _create_list_learning_units_from_containers(list_containers, ac):
        """
        Create the most simple Learning Units list:
        which is one Learning Unit per Container.
        So in this case, four Learning Units are instanciated:
        LUY0, LUY1, LUY2 and LUY3.
        """
        list_lu_year = [
            LearningUnitYearFactory(acronym="LUY%d" % i, learning_container_year=container, academic_year=ac)
            for i, container in enumerate(list_containers)
        ]
        return list_lu_year

    @staticmethod
    def _create_list_entities_version(end_date, start_date):
        """
        Create a list of entities.
            1.  One of them must have a reference to another entity :
                the School entity 'MATH' has the Faculty entity 'SC' as parent (evf_parent_1).
            2.  One of them must have a Sector as direct parent instead of a Faculty :
                the Entity 'BAXR' has the Sector 'SST' as direct parent (evf_parent_2).
        """
        faculty_mec = EntityVersionFactory(
            start_date=start_date,
            acronym="MECA_FACULTY",
            end_date=end_date,
            entity_type=entity_type.FACULTY
        )

        faculty_elme = EntityVersionFactory(
            start_date=start_date,
            acronym="ELME_FACULTY",
            end_date=end_date,
            entity_type=entity_type.FACULTY
        )

        list_entity_version = [
            EntityVersionFactory(entity_type=entity_type.SCHOOL, acronym="MECA", parent=faculty_mec.entity),
            EntityVersionFactory(entity_type=entity_type.SCHOOL, acronym="ELME", parent=faculty_elme.entity)
        ]
        evf_parent_1 = EntityVersionFactory(entity_type=entity_type.FACULTY, acronym="SC")
        evf_child_1 = EntityVersionFactory(entity_type=entity_type.SCHOOL, acronym="MATH", parent=evf_parent_1.entity)
        evf_parent_2 = EntityVersionFactory(entity_type=entity_type.SECTOR, acronym="SST")
        evf_child_2 = EntityVersionFactory(
            entity_type=entity_type.INSTITUTE,
            acronym="BAXR",
            parent=evf_parent_2.entity
        )

        list_entity_version.extend([evf_parent_1, evf_child_1, evf_parent_2, evf_child_2])
        return list_entity_version

    @staticmethod
    def _add_entities_to_containers(list_entity_version, list_lu_container_year):
        """
        Associate the entities to the Learning Units.
        The last Learning Unit LUY2 must be associated with an entity which has a related parent.
        The associations are:
            1. LUY0 -associated to LC0- has 'MECA' for REQUIREMENT Entity
            2. LUY0 -associated to LC0- has 'ELME' for ALLOCATION Entity
            3. LUY1 -associated to LC1- has 'SC' for REQUIREMENT Entity
            4. LUY1 -associated to LC1- has 'MECA' for ALLOCATION Entity
            5. LUY2 -associated to LC2- has 'SC' for REQUIREMENT Entity
            6. LUY2 -associated to LC2- has 'MATH' for ALLOCATION Entity
            7. LUY3 -associated to LC3- has 'BUDR' for REQUIREMENT Entity
            8. LUY3 -associated to LC3- has 'BAXR' for ALLOCATION Entity
        """
        list_lu_container_year[0].requirement_entity = list_entity_version[0].entity
        list_lu_container_year[0].allocation_entity = list_entity_version[1].entity
        list_lu_container_year[0].save()

        list_lu_container_year[0].requirement_entity = list_entity_version[0].entity
        list_lu_container_year[0].allocation_entity = list_entity_version[1].entity
        list_lu_container_year[0].save()

        list_lu_container_year[1].requirement_entity = list_entity_version[2].entity
        list_lu_container_year[1].allocation_entity = list_entity_version[0].entity
        list_lu_container_year[1].save()

        list_lu_container_year[2].requirement_entity = list_entity_version[2].entity
        list_lu_container_year[2].allocation_entity = list_entity_version[3].entity
        list_lu_container_year[2].save()

        list_lu_container_year[3].requirement_entity = list_entity_version[3].entity
        list_lu_container_year[3].allocation_entity = list_entity_version[5].entity
        list_lu_container_year[3].save()

    def test_is_service_course(self):
        self.assertTrue(
            is_service_course(self.current_ac_year, self.list_entity_version[0], self.list_entity_version[1])
        )

    def test_is_service_course_pedagogical_exception(self):
        exception_entity = [
            EntityVersionFactory(
                start_date=self.current_ac_year.start_date, end_date=self.current_ac_year.end_date,
                acronym=acronym, entity_type=entity_type.SCHOOL
            )
            for acronym in PEDAGOGICAL_ENTITY_ADDED_EXCEPTIONS
        ]
        for entity in exception_entity:
            self.assertTrue(
                is_service_course(self.current_ac_year, entity, self.list_entity_version[0])
            )

    def test_is_not_service_course(self):
        self.assertFalse(
            is_service_course(self.current_ac_year, self.list_entity_version[2], self.list_entity_version[3])
        )

    def get_valid_data(self):
        return {
            "academic_year": self.current_ac_year.pk,
            "acronym": "LDROI1001"
        }

    def test_get_service_courses_by_empty_requirement_and_allocation_entity(self):
        form_data = {"academic_year": self.current_ac_year.pk}

        service_course_filter = base.forms.learning_unit.search.service_course.ServiceCourseFilter(form_data)
        self.assertTrue(service_course_filter.is_valid())
        self.assertEqual(
            [self.list_learning_unit_year[0], self.list_learning_unit_year[1]],
            list(service_course_filter.qs)
        )

    def test_get_service_courses_by_allocation_acronym(self):
        form_data = {
            "allocation_entity": self.list_entity_version[1].acronym
        }

        service_course_filter = base.forms.learning_unit.search.service_course.ServiceCourseFilter(form_data)
        self.assertTrue(service_course_filter.is_valid())
        self.assertEqual([self.list_learning_unit_year[0]], list(service_course_filter.qs))

    def test_get_service_courses_by_allocation_acronym_with_no_faculty_as_parent(self):
        form_data = {
            "requirement_entity": self.list_entity_version[3].acronym,
            "allocation_entity": self.list_entity_version[5].acronym
        }

        service_course_filter = base.forms.learning_unit.search.service_course.ServiceCourseFilter(form_data)
        self.assertTrue(service_course_filter.is_valid())
        self.assertEqual(list(service_course_filter.qs), [])

    def test_get_service_courses_by_requirement_acronym(self):
        form_data = {
            "requirement_entity": self.list_entity_version[0].acronym
        }

        service_course_filter = base.forms.learning_unit.search.service_course.ServiceCourseFilter(form_data)
        self.assertTrue(service_course_filter.is_valid())
        self.assertEqual(list(service_course_filter.qs), [self.list_learning_unit_year[0]])

    def test_get_service_courses_by_requirement_and_allocation_acronym(self):
        form_data = {
            "requirement_entity": self.list_entity_version[0].acronym,
            "allocation_entity": self.list_entity_version[1].acronym
        }

        service_course_filter = base.forms.learning_unit.search.service_course.ServiceCourseFilter(form_data)
        self.assertTrue(service_course_filter.is_valid())
        self.assertEqual(len(service_course_filter.qs), 1)

    def test_get_service_courses_by_requirement_and_allocation_acronym_within_same_faculty(self):
        form_data = {
            "requirement_entity": self.list_entity_version[2].acronym,
            "allocation_entity": self.list_entity_version[3].acronym
        }

        service_course_filter = base.forms.learning_unit.search.service_course.ServiceCourseFilter(form_data)
        self.assertTrue(service_course_filter.is_valid())
        self.assertEqual(list(service_course_filter.qs), [])

    def test_search_learning_units_by_tutor(self):
        form_data = {
            "tutor": self.tutor.person.first_name,
        }

        service_course_filter = base.forms.learning_unit.search.simple.LearningUnitFilter(form_data)
        self.assertTrue(service_course_filter.is_valid())
        self.assertEqual(list(service_course_filter.qs), [self.list_learning_unit_year[0]])

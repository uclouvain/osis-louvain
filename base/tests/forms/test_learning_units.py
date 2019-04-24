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
from django.utils import timezone

from attribution.tests.factories.attribution import AttributionNewFactory
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from base.business.learning_unit_year_with_context import is_service_course
from base.forms.learning_unit import search_form
from base.models.enums import entity_container_year_link_type, entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.tutor import TutorFactory
from reference.tests.factories.country import CountryFactory


class TestLearningUnitForm(TestCase):
    def setUp(self):
        self.country = CountryFactory()
        self.academic_yr = AcademicYearFactory(year=timezone.now().year)
        self.start_date = self.academic_yr.start_date
        self.end_date = self.academic_yr.end_date

        self.list_learning_unit_container_year = self._create_list_containers(4)
        self.list_learning_unit_year = self._create_list_learning_units_from_containers(
            self.list_learning_unit_container_year)
        self.list_entity_version = self._create_list_entities_version()
        self.list_entity_container_year = self._create_list_entity_container_years(
            self.list_entity_version,
            self.list_learning_unit_container_year)
        self.tutor = TutorFactory()
        self.attribution = AttributionNewFactory(tutor=self.tutor)
        self.learning_component = LearningComponentYearFactory(learning_unit_year=self.list_learning_unit_year[0])
        self.attribution_charge_new = \
            AttributionChargeNewFactory(attribution=self.attribution,
                                        learning_component_year=self.learning_component)

    def _create_list_containers(self, number_of_containers):
        list_lu_container_year = [
            LearningContainerYearFactory(acronym="LC%d" % container,
                                         academic_year=self.academic_yr)
            for container in range(number_of_containers)
        ]
        return list_lu_container_year

    def _create_list_learning_units_from_containers(self, list_containers):
        """
        Create the most simple Learning Units list:
        which is one Learning Unit per Container.
        So in this case, four Learning Units are instanciated:
        LUY0, LUY1, LUY2 and LUY3.
        """
        list_lu_year = [
            LearningUnitYearFactory(acronym="LUY%d" % i,
                                    learning_container_year=container,
                                    academic_year=self.academic_yr)
            for i, container in enumerate(list_containers)
        ]
        return list_lu_year

    def _create_entity_version(self, **kwargs):
        start_date = kwargs.pop('start_date', self.start_date)
        end_date = kwargs.pop('end_date', self.end_date)
        return EntityVersionFactory(start_date=start_date, end_date=end_date, **kwargs)

    def _create_list_entities_version(self):
        """
        Create a list of entities.
            1.  One of them must have a reference to another entity :
                the School entity 'MATH' has the Faculty entity 'SC' as parent (evf_parent_1).
            2.  One of them must have a Sector as direct parent instead of a Faculty :
                the Entity 'BAXR' has the Sector 'SST' as direct parent (evf_parent_2).
        """
        faculty_meca = self._create_entity_version(entity_type=entity_type.FACULTY, acronym="MECA_FACULTY",
                                                   start_date=self.start_date, end_date=self.end_date)
        faculty_elme = self._create_entity_version(entity_type=entity_type.FACULTY, acronym="ELME_FACULTY",
                                                   start_date=self.start_date, end_date=self.end_date)
        list_entity_version = [
            self._create_entity_version(entity_type=entity_type.SCHOOL, acronym="MECA", parent=faculty_meca.entity),
            self._create_entity_version(entity_type=entity_type.SCHOOL, acronym="ELME", parent=faculty_elme.entity)
        ]
        evf_parent_1 = self._create_entity_version(entity_type=entity_type.FACULTY, acronym="SC")
        evf_child_1 = self._create_entity_version(entity_type=entity_type.SCHOOL, acronym="MATH",
                                                  parent=evf_parent_1.entity)
        evf_parent_2 = self._create_entity_version(entity_type=entity_type.SECTOR, acronym="SST")
        evf_child_2 = self._create_entity_version(entity_type=entity_type.INSTITUTE, acronym="BAXR",
                                                  parent=evf_parent_2.entity)
        list_entity_version.append(evf_parent_1)
        list_entity_version.append(evf_child_1)
        list_entity_version.append(evf_parent_2)
        list_entity_version.append(evf_child_2)
        return list_entity_version

    def _create_list_entity_container_years(self, list_entity_version, list_lu_container_year):
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
        list_entity_container_year = [
            EntityContainerYearFactory(
                entity=list_entity_version[0].entity,
                learning_container_year=list_lu_container_year[0],
                type=entity_container_year_link_type.REQUIREMENT_ENTITY),
            EntityContainerYearFactory(
                entity=list_entity_version[1].entity,
                learning_container_year=list_lu_container_year[0],
                type=entity_container_year_link_type.ALLOCATION_ENTITY),
            EntityContainerYearFactory(
                entity=list_entity_version[2].entity,
                learning_container_year=list_lu_container_year[1],
                type=entity_container_year_link_type.REQUIREMENT_ENTITY),
            EntityContainerYearFactory(
                entity=list_entity_version[0].entity,
                learning_container_year=list_lu_container_year[1],
                type=entity_container_year_link_type.ALLOCATION_ENTITY),
            EntityContainerYearFactory(
                entity=list_entity_version[2].entity,
                learning_container_year=list_lu_container_year[2],
                type=entity_container_year_link_type.REQUIREMENT_ENTITY),
            EntityContainerYearFactory(
                entity=list_entity_version[3].entity,
                learning_container_year=list_lu_container_year[2],
                type=entity_container_year_link_type.ALLOCATION_ENTITY),
            EntityContainerYearFactory(
                entity=list_entity_version[3].entity,
                learning_container_year=list_lu_container_year[3],
                type=entity_container_year_link_type.REQUIREMENT_ENTITY),
            EntityContainerYearFactory(
                entity=list_entity_version[5].entity,
                learning_container_year=list_lu_container_year[3],
                type=entity_container_year_link_type.ALLOCATION_ENTITY)
        ]
        return list_entity_container_year

    def test_is_service_course(self):
        self.assertTrue(
            is_service_course(self.academic_yr, self.list_entity_version[0], self.list_entity_version[1])
        )

    def test_is_not_service_course(self):
        self.assertFalse(
            is_service_course(self.academic_yr, self.list_entity_version[2], self.list_entity_version[3])
        )

    def get_valid_data(self):
        return {
            "academic_year_id": self.academic_yr.pk,
            "acronym": "LDROI1001"
        }

    def test_get_service_courses_by_empty_requirement_and_allocation_entity(self):
        form_data = {}

        form = search_form.LearningUnitYearForm(form_data, service_course_search=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            list(form.get_activity_learning_units()),
            [self.list_learning_unit_year[0], self.list_learning_unit_year[1]]
        )

    def test_get_service_courses_by_allocation_acronym(self):
        form_data = {
            "allocation_entity_acronym": self.list_entity_version[1].acronym
        }

        form = search_form.LearningUnitYearForm(form_data, service_course_search=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(list(form.get_activity_learning_units()), [self.list_learning_unit_year[0]])

    def test_get_service_courses_by_allocation_acronym_with_no_faculty_as_parent(self):
        form_data = {
            "requirement_entity_acronym": self.list_entity_version[3].acronym,
            "allocation_entity_acronym": self.list_entity_version[5].acronym
        }

        form = search_form.LearningUnitYearForm(form_data, service_course_search=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(list(form.get_activity_learning_units()), [])

    def test_get_service_courses_by_requirement_acronym(self):
        form_data = {
            "requirement_entity_acronym": self.list_entity_version[0].acronym
        }

        form = search_form.LearningUnitYearForm(form_data, service_course_search=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(list(form.get_activity_learning_units()), [self.list_learning_unit_year[0]])

    def test_get_service_courses_by_requirement_and_allocation_acronym(self):
        form_data = {
            "requirement_entity_acronym": self.list_entity_version[0].acronym,
            "allocation_entity_acronym": self.list_entity_version[1].acronym
        }

        form = search_form.LearningUnitYearForm(form_data, service_course_search=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.get_activity_learning_units()), 1)

    def test_get_service_courses_by_requirement_and_allocation_acronym_within_same_faculty(self):
        form_data = {
            "requirement_entity_acronym": self.list_entity_version[2].acronym,
            "allocation_entity_acronym": self.list_entity_version[3].acronym
        }

        form = search_form.LearningUnitYearForm(form_data, service_course_search=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(list(form.get_activity_learning_units()), [])

    def test_search_learning_units_by_tutor(self):
        form_data = {
            "tutor": self.tutor.person.first_name,
        }

        form = search_form.LearningUnitYearForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(list(form.get_activity_learning_units()), [self.list_learning_unit_year[0]])

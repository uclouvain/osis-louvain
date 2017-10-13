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
from base.business import learning_unit_year_with_context
from base.models.enums import entity_container_year_link_type as entity_types , organization_type, \
    entity_container_year_link_type
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_component_year import EntityComponentYearFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.academic_year import AcademicYearFactory
import datetime
from django.utils.translation import ugettext_lazy as _

from base.tests.factories.organization import OrganizationFactory
from reference.tests.factories.country import CountryFactory
from decimal import Decimal


class LearningUnitYearWithContextTestCase(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)
        self.learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year)
        self.organization = OrganizationFactory(type=organization_type.MAIN)
        self.country = CountryFactory()
        self.entity = EntityFactory(country=self.country, organization=self.organization)
        self.entity_container_yr = EntityContainerYearFactory(learning_container_year=self.learning_container_yr,
                                                              type=entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                              entity=self.entity)
        self.learning_component_yr = LearningComponentYearFactory(learning_container_year=self.learning_container_yr,
                                                                  hourly_volume_partial=-1, planned_classes=1)
        self.entity_component_yr = EntityComponentYearFactory(learning_component_year=self.learning_component_yr,
                                                              entity_container_year=self.entity_container_yr,
                                                              hourly_volume_total=None)

        self.entity_components_yr = [self.entity_component_yr,]

    def test_get_floated_only_element_of_list(self):
        a_list = []
        self.assertIsNone(learning_unit_year_with_context._get_floated_only_element_of_list(a_list))
        self.assertEquals(learning_unit_year_with_context._get_floated_only_element_of_list(a_list, 0), 0)

        a_list = [17]
        self.assertEquals(learning_unit_year_with_context._get_floated_only_element_of_list(a_list), 17.0)
        self.assertEquals(type(learning_unit_year_with_context._get_floated_only_element_of_list(a_list)), Decimal)

        a_list = [1, 2]
        with self.assertRaisesMessage(ValueError, "The provided list should contain 0 or 1 elements"):
            learning_unit_year_with_context._get_floated_only_element_of_list(a_list)

    def test_get_requirement_entities_volumes(self):
        academic_year = AcademicYearFactory(year=2016)
        learning_container_year = LearningContainerYearFactory(academic_year=academic_year)
        learning_component_year = LearningComponentYearFactory(learning_container_year=learning_container_year)
        entity_types_list = [
            entity_types.REQUIREMENT_ENTITY,
            entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1,
            entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2
        ]
        entity_containers_year = [EntityContainerYearFactory(type=entity_types_list[x],
                                                             learning_container_year=learning_container_year
                                                             ) for x in range(3)]
        components = [EntityComponentYearFactory(entity_container_year=entity_containers_year[x],
                                                 learning_component_year=learning_component_year,
                                                 hourly_volume_total=x+5
                                                 ) for x in range(3)]
        wanted_response = {
            "REQUIREMENT_ENTITY": 5,
            "ADDITIONAL_REQUIREMENT_ENTITY_1": 6,
            "ADDITIONAL_REQUIREMENT_ENTITY_2": 7,
        }

        self.assertDictEqual(learning_unit_year_with_context._get_requirement_entities_volumes(components),
                             wanted_response)

    def test_volumes_unknwon_quadrimester(self):
        self.learning_component_yr.hourly_volume_partial = -1
        self.entity_component_yr.hourly_volume_total = 30

        data = learning_unit_year_with_context.volume_learning_component_year(self.learning_component_yr,
                                                                              self.entity_components_yr)
        self.assertEqual(data.get(learning_unit_year_with_context.TOTAL_VOLUME_KEY), 30)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_QUARTER_KEY), _('partial_or_remaining'))
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_PARTIAL_KEY),
                         learning_unit_year_with_context.VOLUME_FOR_UNKNOWN_QUADRIMESTER)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_REMAINING_KEY),
                         learning_unit_year_with_context.VOLUME_FOR_UNKNOWN_QUADRIMESTER)

    def test_volumes_undefined(self):
        self.learning_component_yr.hourly_volume_partial = None
        self.entity_component_yr.hourly_volume_total = 15

        data = learning_unit_year_with_context.volume_learning_component_year(self.learning_component_yr,
                                                                              self.entity_components_yr)
        self.assertEqual(data.get(learning_unit_year_with_context.TOTAL_VOLUME_KEY), 15)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_QUARTER_KEY),
                         learning_unit_year_with_context.UNDEFINED_VALUE)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_PARTIAL_KEY),
                         learning_unit_year_with_context.UNDEFINED_VALUE)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_REMAINING_KEY),
                         learning_unit_year_with_context.UNDEFINED_VALUE)

    def test_volumes(self):
        self.learning_component_yr.hourly_volume_partial = 0
        self.entity_component_yr.hourly_volume_total = 15
        data = learning_unit_year_with_context.volume_learning_component_year(self.learning_component_yr,
                                                                              self.entity_components_yr)
        self.assertEqual(data.get(learning_unit_year_with_context.TOTAL_VOLUME_KEY), 15)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_QUARTER_KEY), _('remaining'))
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_PARTIAL_KEY), 0)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_REMAINING_KEY), 15)

        self.learning_component_yr.hourly_volume_partial=15
        data = learning_unit_year_with_context.volume_learning_component_year(self.learning_component_yr,
                                                                              self.entity_components_yr)
        self.assertEqual(data.get(learning_unit_year_with_context.TOTAL_VOLUME_KEY), 15)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_PARTIAL_KEY), 15)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_QUARTER_KEY), _('partial'))
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_REMAINING_KEY), 0)

        self.learning_component_yr.hourly_volume_partial=12
        data = learning_unit_year_with_context.volume_learning_component_year(self.learning_component_yr,
                                                                              self.entity_components_yr)
        self.assertEqual(data.get(learning_unit_year_with_context.TOTAL_VOLUME_KEY), 15)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_QUARTER_KEY), _('partial_remaining'))
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_PARTIAL_KEY), 12)
        self.assertEqual(data.get(learning_unit_year_with_context.VOLUME_REMAINING_KEY), 3)

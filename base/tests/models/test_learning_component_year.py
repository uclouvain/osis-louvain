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

from base.models.enums import entity_container_year_link_type as entity_types
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory


class LearningUnitYearWithContextTestCase(TestCase):
    def setUp(self):
        self.component_with_repartition = LearningComponentYearFactory(
            hourly_volume_total_annual=15.0,
            planned_classes=3,
            repartition_volume_requirement_entity=20.0,
            repartition_volume_additional_entity_1=10.0,
            repartition_volume_additional_entity_2=15.0,
        )
        self.component_without_repartition = LearningComponentYearFactory(
            hourly_volume_total_annual=15.0,
            planned_classes=3,
            repartition_volume_requirement_entity=None,
            repartition_volume_additional_entity_1=None,
            repartition_volume_additional_entity_2=None,
        )

    def test_repartition_volumes_property(self):
        entity_types_list = [
            entity_types.REQUIREMENT_ENTITY,
            entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1,
            entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2
        ]
        entity_containers_year = [
            EntityContainerYearFactory(
                type=entity_types_list[x],
                learning_container_year=self.component_with_repartition.learning_unit_year.learning_container_year
            ) for x in range(3)
        ]
        expected_result = {
            "REQUIREMENT_ENTITY": 20.0,
            "ADDITIONAL_REQUIREMENT_ENTITY_1": 10.0,
            "ADDITIONAL_REQUIREMENT_ENTITY_2": 15.0,
        }

        self.assertDictEqual(self.component_with_repartition.repartition_volumes, expected_result)

        expected_result = {
            "REQUIREMENT_ENTITY": 0.0,
            "ADDITIONAL_REQUIREMENT_ENTITY_1": 0.0,
            "ADDITIONAL_REQUIREMENT_ENTITY_2": 0.0,
        }
        self.assertDictEqual(self.component_without_repartition.repartition_volumes, expected_result)

    def test_vol_global(self):
        self.assertIsInstance(self.component_with_repartition.vol_global, float)
        self.assertEqual(self.component_with_repartition.vol_global, 45.0)

    def test_vol_global_when_repartition_volumes_are_none(self):
        self.assertIsInstance(self.component_without_repartition.vol_global, float)
        self.assertEqual(self.component_without_repartition.vol_global, 45.0)

    def test_get_repartition_volume(self):
        repartition_value = self.component_with_repartition.get_repartition_volume(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1)
        self.assertEqual(repartition_value, 10.0)

    def test_set_repartition_volume(self):
        new_repartition_value = 1.0

        self.component_without_repartition.set_repartition_volume(entity_types.REQUIREMENT_ENTITY, new_repartition_value)
        self.assertEqual(self.component_without_repartition.repartition_volume_requirement_entity, new_repartition_value)

        self.component_without_repartition.set_repartition_volume(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, new_repartition_value)
        self.assertEqual(self.component_without_repartition.repartition_volume_requirement_entity, new_repartition_value)

        self.component_without_repartition.set_repartition_volume(entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, new_repartition_value)
        self.assertEqual(self.component_without_repartition.repartition_volume_requirement_entity, new_repartition_value)

        self.component_without_repartition.refresh_from_db()

    def test_set_repartition_volumes(self):
        new_repartition_volumes = {
            entity_types.REQUIREMENT_ENTITY: 1.0,
            entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1: 2.0,
            entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2: 3.0,
        }
        self.component_without_repartition.set_repartition_volumes(new_repartition_volumes)
        self.assertEqual(self.component_without_repartition.repartition_volume_requirement_entity, 1.0)
        self.assertEqual(self.component_without_repartition.repartition_volume_additional_entity_1, 2.0)
        self.assertEqual(self.component_without_repartition.repartition_volume_additional_entity_2, 3.0)
        self.component_without_repartition.refresh_from_db()

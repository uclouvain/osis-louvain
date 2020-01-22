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

from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_1, ADDITIONAL_REQUIREMENT_ENTITY_2
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory


class LearningContainerYearAttributesTestMixin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.requirement_entity = EntityVersionFactory().entity
        cls.allocation_entity = EntityVersionFactory().entity
        cls.additional_entity_1 = EntityVersionFactory().entity
        cls.additional_entity_2 = EntityVersionFactory().entity

    def setUp(self):
        self.container_year = LearningContainerYearFactory(
            requirement_entity=self.requirement_entity,
            allocation_entity=self.allocation_entity,
            additional_entity_1=self.additional_entity_1,
            additional_entity_2=self.additional_entity_2,
        )


class GetEntityByTypeTest(LearningContainerYearAttributesTestMixin):
    """Unit tests on LearningContainerYear.get_entity_from_type()"""
    def test_common_usage(self):
        self.assertEqual(self.container_year.get_entity_from_type(REQUIREMENT_ENTITY), self.requirement_entity)
        self.assertEqual(self.container_year.get_entity_from_type(ALLOCATION_ENTITY), self.allocation_entity)
        self.assertEqual(self.container_year.get_entity_from_type(ADDITIONAL_REQUIREMENT_ENTITY_1),
                         self.additional_entity_1)
        self.assertEqual(self.container_year.get_entity_from_type(ADDITIONAL_REQUIREMENT_ENTITY_2),
                         self.additional_entity_2)

    def test_when_entity_is_not_set(self):
        self.container_year.additional_entity_2 = None
        self.container_year.save()
        self.assertIsNone(self.container_year.get_entity_from_type(ADDITIONAL_REQUIREMENT_ENTITY_2))

    def test_when_inexisting_entity_type(self):
        with self.assertRaises(KeyError):
            self.container_year.get_entity_from_type("ADDITIONAL_ENTITY_3")


class GetMapEntityByTypeTest(LearningContainerYearAttributesTestMixin):
    """Unit tests on LearningContainerYear.get_map_entity_by_type()"""
    def test_common_usage(self):
        expected_result = {
            REQUIREMENT_ENTITY: self.requirement_entity,
            ALLOCATION_ENTITY: self.allocation_entity,
            ADDITIONAL_REQUIREMENT_ENTITY_1: self.additional_entity_1,
            ADDITIONAL_REQUIREMENT_ENTITY_2: self.additional_entity_2,
        }
        self.assertDictEqual(self.container_year.get_map_entity_by_type(), expected_result)


class SetEntityTest(LearningContainerYearAttributesTestMixin):
    """Unit tests on LearningContainerYear.set_entity()"""
    def test_common_usage(self):
        new_entity = EntityVersionFactory().entity
        self.container_year.set_entity(ADDITIONAL_REQUIREMENT_ENTITY_2, new_entity)
        self.assertEqual(self.container_year.additional_entity_2, new_entity)

        self.container_year.refresh_from_db()
        # Assert object is not persisted in DB
        self.assertEqual(self.container_year.additional_entity_2, self.additional_entity_2)

    def test_when_inexisting_entity_type(self):
        with self.assertRaises(KeyError):
            self.container_year.set_entity("ADDITIONAL_ENTITY_3", EntityVersionFactory().entity)


class SetEntitiesTest(LearningContainerYearAttributesTestMixin):
    """Unit tests on LearningContainerYear.set_entities()"""
    def test_common_usage(self):
        new_requirement_entity = EntityVersionFactory().entity
        new_allocation_entity = EntityVersionFactory().entity
        new_entities = {
            REQUIREMENT_ENTITY: new_requirement_entity,
            ALLOCATION_ENTITY: new_allocation_entity,
        }
        self.container_year.set_entities(new_entities)
        self.assertEqual(self.container_year.requirement_entity, new_requirement_entity)
        self.assertEqual(self.container_year.allocation_entity, new_allocation_entity)

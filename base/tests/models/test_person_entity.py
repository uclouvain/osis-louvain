##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.test import TestCase

from base.models import person_entity
from base.models.person_entity import PersonEntity
from base.models.utils import person_entity_filter
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory


class PersonEntityTest(TestCase):
    def setUp(self):
        self._create_entity_structure()

    def test_create_same_person_same_entity_multiple_time(self):
        """ Must raise an error, because db constraint on person/entity"""
        person = PersonFactory()
        PersonEntityFactory(person=person, entity=self.root_entity)
        with self.assertRaises(IntegrityError):
            PersonEntityFactory(person=person, entity=self.root_entity)

    def test_find_entities_by_person_with_no_link(self):
        person = PersonFactory()
        entities = person_entity.find_entities_by_person(person)
        self.assertIsInstance(entities, list)
        self.assertFalse(entities)

    def test_find_entities_by_person_with_child_false(self):
        person = PersonFactory()
        PersonEntityFactory(person=person, entity=self.root_entity, with_child=False)
        entities = person_entity.find_entities_by_person(person)
        self.assertIsInstance(entities, list)
        self.assertEqual(len(entities), 1)  # We take only root, no child

    def test_find_entities_by_person_with_child_true(self):
        person = PersonFactory()
        PersonEntityFactory(person=person, entity=self.root_entity, with_child=True)
        entities = person_entity.find_entities_by_person(person)
        self.assertIsInstance(entities, list)
        self.assertEqual(len(entities), 8)

    def test_find_entities_by_person_with_multiple_person_entity(self):
        person = PersonFactory()
        PersonEntityFactory(person=person, entity=self.sst_entity, with_child=True)
        PersonEntityFactory(person=person, entity=self.ssh_entity, with_child=False)
        entities = person_entity.find_entities_by_person(person)
        self.assertIsInstance(entities, list)
        self.assertEqual(len(entities), 4)

    def test_find_entities_by_person_with_multiple_person_entity_no_duplicate(self):
        person = PersonFactory()
        PersonEntityFactory(person=person, entity=self.sst_entity, with_child=True)
        PersonEntityFactory(person=person, entity=self.agro_entity, with_child=False)
        entities = person_entity.find_entities_by_person(person)
        self.assertIsInstance(entities, list)
        self.assertEqual(len(entities), 3)

    def test_filter_by_attached_entities(self):
        person = PersonFactory()
        PersonEntityFactory(person=person, entity=self.sst_entity, with_child=True)
        PersonEntityFactory(person=person, entity=self.agro_entity, with_child=False)
        person_2 = PersonFactory()
        PersonEntityFactory(person=person_2, entity=self.ssh_entity, with_child=True)
        queryset = PersonEntity.objects.all()
        list_filtered = list(person_entity_filter.filter_by_attached_entities(person, queryset))
        self.assertEqual(len(list_filtered), 2)
        list_filtered = list(person_entity_filter.filter_by_attached_entities(person_2, queryset))
        self.assertEqual(len(list_filtered), 1)

    def test_filter_by_attached_entities_not_defined_model(self):
        person_2 = PersonFactory()
        queryset = User.objects.all()
        with self.assertRaises(ObjectDoesNotExist):
            person_entity_filter.filter_by_attached_entities(person_2, queryset)

    def _create_entity_structure(self):
        self.organization = OrganizationFactory(name="Université catholique de Louvain", acronym="UCL")
        # Create entities UCL
        self.root_entity = _create_entity_and_version_related_to(self.organization, "UCL")
        # SST entity
        self.sst_entity = _create_entity_and_version_related_to(self.organization, "SST", self.root_entity)
        self.agro_entity = _create_entity_and_version_related_to(self.organization, "AGRO", self.sst_entity)
        self.chim_entity = _create_entity_and_version_related_to(self.organization, "CHIM", self.sst_entity)
        # SSH entity
        self.ssh_entity = _create_entity_and_version_related_to(self.organization, "SSH", self.root_entity)
        self.fial_entity = _create_entity_and_version_related_to(self.organization, "FIAL", self.ssh_entity)
        # SSS entity
        self.sss_entity = _create_entity_and_version_related_to(self.organization, "SSS", self.root_entity)
        self.fasb_entity = _create_entity_and_version_related_to(self.organization, "FASB", self.sss_entity)


def _create_entity_and_version_related_to(organization, acronym, parent=None):
    entity = EntityFactory(organization=organization)
    EntityVersionFactory(acronym=acronym, entity=entity, parent=parent, end_date=None)
    return entity

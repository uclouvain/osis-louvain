##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
import datetime

import factory
import factory.fuzzy
from django.test import TestCase
from django.utils import timezone

from base.models import entity
from base.models.entity import find_versions_from_entites
from base.models.entity_version import EntityVersion
from base.models.enums import entity_type
from base.tests.factories.entity import EntityFactory, EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from reference.tests.factories.country import CountryFactory


class EntityTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.start_date = timezone.make_aware(datetime.datetime(2015, 1, 1))
        cls.end_date = timezone.make_aware(datetime.datetime(2015, 12, 31))
        cls.date_in_2015 = factory.fuzzy.FuzzyDate(timezone.make_aware(datetime.datetime(2015, 1, 1)),
                                                   timezone.make_aware(datetime.datetime(2015, 12, 30))).fuzz()
        cls.date_in_2017 = factory.fuzzy.FuzzyDate(timezone.make_aware(datetime.datetime(2017, 1, 1)),
                                                   timezone.make_aware(datetime.datetime(2017, 12, 30))).fuzz()
        cls.country = CountryFactory()
        cls.parent = EntityWithVersionFactory(
            country=cls.country,
            version__acronym="ROOT_ENTITY",
            version__start_date=cls.start_date,
            version__end_date=cls.end_date
        )
        cls.types_dict = dict(entity_type.ENTITY_TYPES)
        types = [cls.types_dict['SECTOR'],
                 cls.types_dict['FACULTY'],
                 cls.types_dict['SCHOOL'],
                 cls.types_dict['FACULTY']]
        cls.children = [
            EntityWithVersionFactory(
                country=cls.country,
                version__parent=cls.parent,
                version__acronym="ENTITY_V_" + str(x),
                version__start_date=cls.start_date,
                version__end_date=cls.end_date,
                version__entity_type=types[x]
            ) for x in range(4)
        ]

        cls.an_entity = EntityFactory(external_id="1234567")

    def test_search_entities_by_version_acronym_date_in(self):
        self.assertCountEqual(entity.search(acronym='ENTITY_V', version_date=self.date_in_2015), self.children)
        self.assertCountEqual(entity.search(acronym='NON_EXISTING', version_date=self.date_in_2015), [])
        self.assertCountEqual(entity.search(acronym='ENTITY_V_1', version_date=self.date_in_2015), [self.children[1]])

    def test_search_entities_by_version_acronym_date_out(self):
        self.assertCountEqual(entity.search(acronym='ENTITY_V', version_date=self.date_in_2017), [])
        self.assertCountEqual(entity.search(acronym='NON_EXISTING', version_date=self.date_in_2017), [])
        self.assertCountEqual(entity.search(acronym='ENTITY_V_1', version_date=self.date_in_2017), [])

    def test_get_by_external_id(self):
        self.assertEqual(entity.get_by_external_id("1234567"), self.an_entity)
        self.assertEqual(entity.get_by_external_id("321"), None)

    def test_get_by_internal_id(self):
        self.assertEqual(entity.get_by_internal_id(self.an_entity.id), self.an_entity)
        self.assertEqual(entity.get_by_internal_id(self.an_entity.id + 1), None)

    def test_find_descendants_with_parent(self):
        entities_with_descendants = EntityVersion.objects.get_tree([self.parent], date=self.date_in_2015)
        self.assertEqual(len(entities_with_descendants), 5)

    def test_find_descendants_out_date(self):
        entities_with_descendants = EntityVersion.objects.get_tree([self.parent], date=self.date_in_2017)
        self.assertEqual(len(entities_with_descendants), 1)

    def test_find_descendants_with_multiple_parent(self):
        parent_2 = EntityWithVersionFactory(
            country=self.country,
            version__acronym="ROOT_ENTITY_2",
            version__start_date=self.start_date,
            version__end_date=self.end_date
        )
        EntityWithVersionFactory(
            country=self.country,
            version__acronym="CHILD_OF_ROOT_2",
            version__start_date=self.start_date,
            version__end_date=self.end_date
        )
        EntityWithVersionFactory(
            country=self.country,
            version__acronym="CHILD_OF_CHILD",
            version__start_date=self.start_date,
            version__end_date=self.end_date
        )
        entities_with_descendants = EntityVersion.objects.get_tree([self.parent, parent_2], date=self.date_in_2015)
        self.assertEqual(len(entities_with_descendants), 6)

    def test_most_recent_acronym(self):
        most_recent_year = 2018
        for year in range(2016, most_recent_year + 1):
            date = datetime.date(year=year, month=1, day=1)
            EntityVersionFactory(entity_id=self.an_entity.id, start_date=date)
        most_recent_date = datetime.date(year=most_recent_year, month=1, day=1)
        most_recent_entity_version = EntityVersion.objects.get(start_date=most_recent_date,
                                                               entity=self.an_entity)
        self.assertEqual(self.an_entity.most_recent_acronym, most_recent_entity_version.acronym)

    def test_find_versions_from_entites_with_date(self):
        entities_list = find_versions_from_entites([self.parent.id], self.start_date)
        self.assertEqual(len(entities_list), 1)

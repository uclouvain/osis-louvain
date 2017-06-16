##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
import factory
import factory.fuzzy
import datetime
from django.utils import timezone
from base.models import entity
from base.models.enums import entity_type
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


class EntityTest(TestCase):

    def setUp(self):
        self.start_date = timezone.make_aware(datetime.datetime(2015, 1, 1))
        self.end_date = timezone.make_aware(datetime.datetime(2015, 12, 31))
        self.date_in_2015 = factory.fuzzy.FuzzyDate(timezone.make_aware(datetime.datetime(2015, 1, 1)),
                                                    timezone.make_aware(datetime.datetime(2015, 12, 30))).fuzz()
        self.date_in_2017 = factory.fuzzy.FuzzyDate(timezone.make_aware(datetime.datetime(2017, 1, 1)),
                                                    timezone.make_aware(datetime.datetime(2017, 12, 30))).fuzz()
        self.parent = EntityFactory()
        self.children = [EntityFactory() for x in range(4)]
        self.types_dict = dict(entity_type.ENTITY_TYPES)
        types = [self.types_dict['SECTOR'],
                 self.types_dict['FACULTY'],
                 self.types_dict['SCHOOL'],
                 self.types_dict['FACULTY']]

        for x in range(4):
            EntityVersionFactory(
                entity=self.children[x],
                parent=self.parent,
                acronym="ENTITY_V_" + str(x),
                start_date=self.start_date,
                end_date=self.end_date,
                entity_type=types[x]
                )

    def test_search_entities_by_version_acronym_date_in(self):
        self.assertCountEqual(entity.search(acronym='ENTITY_V', version_date=self.date_in_2015), self.children)
        self.assertCountEqual(entity.search(acronym='NON_EXISTING', version_date=self.date_in_2015), [])
        self.assertCountEqual(entity.search(acronym='ENTITY_V_1', version_date=self.date_in_2015), [self.children[1]])

    def test_search_entities_by_version_acronym_date_out(self):
        self.assertCountEqual(entity.search(acronym='ENTITY_V', version_date=self.date_in_2017), [])
        self.assertCountEqual(entity.search(acronym='NON_EXISTING', version_date=self.date_in_2017), [])
        self.assertCountEqual(entity.search(acronym='ENTITY_V_1', version_date=self.date_in_2017), [])

    def test_get_by_external_id(self):
        an_entity = EntityFactory(external_id="1234567")
        self.assertEqual(entity.get_by_external_id("1234567"), an_entity)
        self.assertEqual(entity.get_by_external_id("321"), None)

    def test_get_by_internal_id(self):
        an_entity = EntityFactory()
        self.assertEqual(entity.get_by_internal_id(an_entity.id), an_entity)
        self.assertEqual(entity.get_by_internal_id(an_entity.id+1), None)


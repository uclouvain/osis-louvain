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
from datetime import timedelta

from django.test import TestCase

from base.business.entity import get_entities_ids
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


class EntityTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()

    def test_get_entities_ids(self):
        entity_parent = EntityFactory()
        entities = []
        for i in range(20):
            child_entity_version = EntityVersionFactory(
                parent=entity_parent,
                acronym='TEST{}'.format(i),
                start_date=self.current_academic_year.start_date+timedelta(days=i),
                end_date=self.current_academic_year.start_date+timedelta(days=i)
            )
            entity_parent = child_entity_version.entity
            entities.append(entity_parent.id)
        entities_ids = get_entities_ids('NOTHING', True)
        self.assertEqual([], entities_ids)
        entities_ids = get_entities_ids('TEST', True)
        self.assertEqual(entities, sorted(entities_ids))

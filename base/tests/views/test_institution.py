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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.user import UserFactory
from django.core.urlresolvers import reverse
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from base.views import institution


class EntityViewTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.entity = EntityFactory()
        self.parent = EntityFactory()
        self.start_date = datetime.date(2015, 1, 1)
        self.end_date = datetime.date(2015, 12, 31)

        self.entity_version = EntityVersionFactory(
            entity=self.entity,
            acronym="ENTITY_CHILDREN",
            title="This is the entity version ",
            entity_type="FACULTY",
            parent=self.parent,
            start_date=self.start_date,
            end_date=self.end_date
        )
        self.parent_entity_version = EntityVersionFactory(
            entity=self.parent,
            acronym="ENTITY_PARENT",
            title="This is the entity parent version",
            entity_type="SECTOR",
            start_date=self.start_date,
            end_date=self.end_date
        )

    def test_entities(self):
        self.client.force_login(self.user)
        url = reverse('entities')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_entities_search(self):
        self.client.force_login(self.user)
        url = reverse('entities_search')
        response = self.client.get(url+"?acronym=%s&title=%s&type_choices=%s" % ("ENTITY_CHILDREN", "", ""))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context[-1]['entities_version']), 1)

    def test_entity_read(self):
        self.client.force_login(self.user)
        url = reverse('entity_read', args=[self.entity_version.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_entity_diagram(self):
        self.client.force_login(self.user)
        url = reverse('entity_diagram', args=[self.entity_version.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

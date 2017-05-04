
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
from django.test import TestCase, Client
from base.models.person import Person
import json


class GetPersonsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.person = Person.objects.create(first_name='person1', last_name='tests', email='person1@tests.com')
        self.person.save()
        self.person = Person.objects.create(first_name='person2', last_name='tests', email='person2@tests.com')
        self.person.save()


    def test_get_persons(self):
        response = self.client.generic(method='get', path='/assistants/api/get_persons/?term=on2',
                                       HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data[0]['value'], 'person2@tests.com')
        self.assertEqual(len(data), 1)

        response = self.client.generic(method='get', path='/assistants/api/get_persons/?term=tests',
                                       HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(data), 2)

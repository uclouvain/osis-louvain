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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
import json
from unittest import mock

from django.http import HttpResponseForbidden, HttpResponse
from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from base.views import institution


class EntityViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = PersonFactory().user
        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.academic_calendar = OpenAcademicCalendarFactory(
            academic_year=cls.current_academic_year,
            data_year=cls.current_academic_year,
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
        )
        cls.start_date = datetime.date.today() - datetime.timedelta(weeks=48)
        cls.end_date = datetime.date.today() + datetime.timedelta(weeks=48)

        cls.entity_version = EntityVersionFactory(
            acronym="ENTITY_CHILDREN",
            title="This is the entity version ",
            entity_type="FACULTY",
            start_date=cls.start_date,
            end_date=cls.end_date
        )
        cls.parent_entity_version = EntityVersionFactory(
            entity=cls.entity_version.parent,
            acronym="ENTITY_PARENT",
            title="This is the entity parent version",
            entity_type="SECTOR",
            start_date=cls.start_date,
            end_date=cls.end_date
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_entities(self):
        url = reverse('entities')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_entities_search(self):
        url = reverse(institution.entities_search)
        response = self.client.get(url, data={"acronym": "ENTITY_CHILDREN", "title": "", "entity_type": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['entities_version']), 1)

    def test_entity_read(self):
        url = reverse(institution.entity_read, args=[self.entity_version.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['entity_version'], self.entity_version)
        self.assertEqual(context['entity_parent'], self.parent_entity_version)
        self.assertFalse(context['descendants'])
        self.assertDictEqual(
            context['calendar_summary_course_submission'],
            {
                'start_date': self.academic_calendar.start_date,
                'end_date': self.academic_calendar.end_date
            }
        )

    def test_entity_diagram(self):
        url = reverse('entity_diagram', args=[self.entity_version.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @mock.patch('base.models.entity_version.find_by_id')
    @mock.patch('django.contrib.auth.decorators')
    def test_get_entity_address(self, mock_decorators, mock_find_by_id):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        entity = EntityFactory()
        entity_version = EntityVersionFactory(entity=entity, acronym='SSH', title='Sector of sciences', end_date=None)
        mock_find_by_id.return_value = entity_version
        request = mock.Mock(method='GET')
        response = institution.get_entity_address(request, entity_version.id)
        address_data = ['location', 'postal_code', 'city', 'country_id', 'phone', 'fax']
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertTrue(data.get('entity_version_exists_now'))
        self.assertIsNotNone(data.get('recipient'))
        for field_name in address_data:
            self.assertEqual(getattr(entity, field_name), data['address'].get(field_name))

    @mock.patch('base.models.entity_version.find_by_id')
    @mock.patch('django.contrib.auth.decorators')
    def test_get_entity_address_case_no_current_entity_version_exists(self, mock_decorators, mock_find_by_id):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        entity = EntityFactory()
        entity_version = EntityVersionFactory(entity=entity,
                                              acronym='SSH',
                                              title='Sector of sciences',
                                              start_date=datetime.datetime(year=2004, month=1, day=1).date(),
                                              end_date=datetime.datetime(year=2010, month=1, day=1).date())
        mock_find_by_id.return_value = entity_version
        request = mock.Mock(method='GET')
        response = institution.get_entity_address(request, entity_version.id)
        address_data = ['location', 'postal_code', 'city', 'country_id', 'phone', 'fax']
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertFalse(data.get('entity_version_exists_now'))
        self.assertIsNotNone(data.get('recipient'))
        for field_name in address_data:
            self.assertEqual(getattr(entity, field_name), data['address'].get(field_name))


class InstitutionViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory("is_institution_administrator")
        cls.url = reverse('institution')

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_with_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_when_user_has_not_permission(self):
        a_person = PersonFactory()
        self.client.force_login(a_person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_context_contains_mandatory_keys(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTrue('section' in response.context)
        self.assertTrue('view_academicactors' in response.context)

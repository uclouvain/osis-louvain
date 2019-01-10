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
from unittest import mock

import requests
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseNotFound, HttpResponse
from django.test import TestCase, override_settings
from requests import Timeout

from base.business.education_groups import general_information
from base.business.education_groups.general_information import PublishException, RelevantSectionException
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.education_group_year import TrainingFactory


@override_settings(URL_TO_PORTAL_UCL="http://portal-url.com", ESB_API_URL="api.esb.com",
                   ESB_AUTHORIZATION="Basic dummy:1234", ESB_REFRESH_PEDAGOGY_ENDPOINT="offer/{year}/{code}/refresh")
class TestPublishGeneralInformation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()
        cls.training = TrainingFactory()

    @override_settings(ESB_REFRESH_PEDAGOGY_ENDPOINT=None)
    def test_publish_case_missing_settings(self):
        with self.assertRaises(ImproperlyConfigured):
            general_information.publish(self.training)

    @mock.patch('requests.get', return_value=HttpResponseNotFound)
    def test_publish_case_not_found_raise_exception(self, mock_requests):
        with self.assertRaises(PublishException):
            general_information.publish(self.training)

    @mock.patch('requests.get', side_effect=Timeout)
    def test_publish_case_timout_reached(self, mock_requests):
        with self.assertRaises(PublishException):
            general_information.publish(self.training)

    @mock.patch('requests.get', return_value=HttpResponse)
    def test_publish_case_success(self, mock_requests):
        url_portal = general_information.publish(self.training)
        self.assertIsInstance(url_portal, str)


@override_settings(URL_TO_PORTAL_UCL="http://portal-url.com", GET_SECTION_PARAM="sectionsParams")
class TestGetRelevantSections(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()
        cls.training = TrainingFactory()

    @override_settings(GET_SECTION_PARAM=None)
    def test_get_relevant_sections_case_missing_settings(self):
        with self.assertRaises(ImproperlyConfigured):
            general_information.get_relevant_sections(self.training)

    @mock.patch('requests.get', side_effect=Timeout)
    def test_get_relevant_sections_case_timout_reached(self, mock_requests):
        with self.assertRaises(RelevantSectionException):
            general_information.get_relevant_sections(self.training)

    @mock.patch('requests.get', side_effect=requests.exceptions.ConnectionError)
    def test_get_relevant_sections_case_connection_error(self, mock_requests):
        with self.assertRaises(RelevantSectionException):
            general_information.get_relevant_sections(self.training)

    @mock.patch('requests.get')
    def test_get_relevant_sections_case_success_with_sections(self, mock_requests):
        expected_sections = ['test1', 'test2']

        mock_requests.return_value.status_code = HttpResponse.status_code
        mock_requests.return_value.json.return_value = {'sections': expected_sections}

        sections = general_information.get_relevant_sections(self.training)
        self.assertEqual(sections, expected_sections)

    @mock.patch('requests.get')
    def test_get_relevant_sections_case_success_without_sections_in_response(self, mock_requests):
        mock_requests.return_value.status_code = HttpResponse.status_code
        mock_requests.return_value.json.return_value = {'dummy_data': 'dummy'}

        sections = general_information.get_relevant_sections(self.training)
        self.assertListEqual(sections, [])

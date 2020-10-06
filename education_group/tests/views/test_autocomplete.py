##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
import json

from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_categories import TRAINING, MINI_TRAINING, GROUP
from base.tests.factories.certificate_aim import CertificateAimFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory, MiniTrainingEducationGroupTypeFactory,\
    GroupEducationGroupTypeFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import SuperUserFactory


class TestEducationGroupTypeAutoComplete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.trainings = EducationGroupTypeFactory.create_batch(2)
        cls.minitrainings = MiniTrainingEducationGroupTypeFactory.create_batch(3)
        cls.groups = GroupEducationGroupTypeFactory.create_batch(1)

        cls.url = reverse("education_group_type_autocomplete")
        cls.person = PersonFactory()

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_without_category(self):
        response = self.client.get(self.url)
        json_response = response.json()
        self.assertEqual(6, len(json_response["results"]))

    def test_with_category_set(self):
        tuples_category_with_expected_result = [(TRAINING, 2), (MINI_TRAINING, 3), (GROUP, 1)]
        for category, expected_result in tuples_category_with_expected_result:
            with self.subTest(category=category):
                response = self.client.get(self.url, data={"forward": json.dumps({"category": category})})
                json_response = response.json()
                self.assertEqual(expected_result, len(json_response["results"]))

    def test_with_search_query_case_insentive_on_display_value_set(self):
        education_group_type = self.trainings[0]
        search_term = education_group_type.get_name_display().upper()

        response = self.client.get(self.url, data={"forward": json.dumps({"category": TRAINING}), "q": search_term})
        json_response = response.json()

        expected_response = {
            'id': str(education_group_type.pk),
            'selected_text': education_group_type.get_name_display(),
            'text': education_group_type.get_name_display()
        }
        self.assertEqual(len(json_response["results"]), 1)
        self.assertEqual(json_response["results"][0], expected_response)


class TestCertificateAimAutocomplete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.super_user = SuperUserFactory()
        cls.url = reverse("certificate_aim_autocomplete")
        cls.certificate_aim = CertificateAimFactory(
            code=1234,
            section=5,
            description="description",
        )

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url, data={'q': '1234'})
        json_response = str(response.content, encoding='utf8')
        results = json.loads(json_response)['results']
        self.assertEqual(results, [])

    def test_when_param_is_digit_assert_searching_on_code(self):
        # When searching on "code"
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': '1234'})
        self._assert_result_is_correct(response)

    def test_assert_searching_on_description(self):
        # When searching on "description"
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': 'descr'})
        self._assert_result_is_correct(response)

    def test_with_filter_by_section(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'forward': '{"section": "5"}'})
        self._assert_result_is_correct(response)

    def _assert_result_is_correct(self, response):
        self.assertEqual(response.status_code, 200)
        json_response = str(response.content, encoding='utf8')
        results = json.loads(json_response)['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.certificate_aim.code)

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
from collections import OrderedDict

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_achievement import LearningAchievementFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from learning_unit.api.views.learning_achievement import LearningAchievementList
from reference.models.language import FR_CODE_LANGUAGE
from reference.tests.factories.language import FrenchLanguageFactory


class LearningAchievementListTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year
        )

        cls.achievements = []
        for index in range(0, 5):
            cls.achievements.append(
                LearningAchievementFactory(
                    learning_unit_year=cls.learning_unit_year,
                    language=FrenchLanguageFactory(),
                    order=index
                )
            )

        cls.person = PersonFactory()
        url_kwargs = {
            'acronym': cls.learning_unit_year.acronym,
            'year': cls.learning_unit_year.academic_year.year
        }
        cls.url = reverse('learning_unit_api_v1:' + LearningAchievementList.name, kwargs=url_kwargs)

    def setUp(self):
        self.client.force_authenticate(user=self.person.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_results_case_learning_unit_year_not_found(self):
        invalid_url = reverse(
            'learning_unit_api_v1:' + LearningAchievementList.name,
            kwargs={'acronym': 'ACRO', 'year': 2019}
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_results_ensure_order(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 5)

        expected_response = OrderedDict([
            ('code_name', self.achievements[0].code_name),
            ('achievement', self.achievements[0].text),
        ])
        self.assertDictEqual(response.data[0], expected_response)

    def test_get_only_achievements_with_text(self):
        LearningAchievementFactory(
            learning_unit_year=self.learning_unit_year,
            language__code=FR_CODE_LANGUAGE,
            order=5,
            text=''
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 5)

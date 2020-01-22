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

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.business.learning_unit import CMS_LABEL_PEDAGOGY, CMS_LABEL_SPECIFICATIONS
from base.models.enums import learning_unit_year_subtypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from cms.models.translated_text import TranslatedText
from cms.tests.factories.translated_text import TranslatedTextFactory, TranslatedTextRandomFactory
from learning_unit.api.views.summary_specification import LearningUnitSummarySpecification


class LearningUnitSummarySpecificationTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )
        for label in CMS_LABEL_PEDAGOGY:
            TranslatedTextRandomFactory(
                reference=cls.learning_unit_year.pk,
                text_label__label=label,
                language=settings.LANGUAGE_CODE_FR
            )

        cls.person = PersonFactory()
        url_kwargs = {
            'acronym': cls.learning_unit_year.acronym,
            'year': cls.learning_unit_year.academic_year.year
        }
        cls.url = reverse('learning_unit_api_v1:' + LearningUnitSummarySpecification.name, kwargs=url_kwargs)

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
            'learning_unit_api_v1:' + LearningUnitSummarySpecification.name,
            kwargs={'acronym': 'ACRO', 'year': 2019}
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_results_ensure_keys_are_always_present(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_keys = set(CMS_LABEL_PEDAGOGY + CMS_LABEL_SPECIFICATIONS)

        diff = set(response.data.keys()) - expected_keys
        self.assertFalse(diff)

    def test_get_results_ensure_text_from_parent_if_partim_info_empty(self):
        partim = LearningUnitYearFactory(
            acronym=self.learning_unit_year.acronym + 'A',
            academic_year=self.academic_year,
            learning_container_year=self.learning_unit_year.learning_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
        )
        partims_labels = CMS_LABEL_PEDAGOGY + CMS_LABEL_SPECIFICATIONS
        partims_labels.remove('resume')
        for label in partims_labels:
            TranslatedTextFactory(
                reference=partim.pk,
                text_label__label=label,
                language=settings.LANGUAGE_CODE_FR
            )

        url_kwargs = {
            'acronym': partim.acronym,
            'year': partim.academic_year.year
        }
        url = reverse('learning_unit_api_v1:' + LearningUnitSummarySpecification.name, kwargs=url_kwargs)
        response = self.client.get(url)

        expected_keys = set(CMS_LABEL_PEDAGOGY + CMS_LABEL_SPECIFICATIONS)

        diff = set(response.data.keys()) - expected_keys
        self.assertFalse(diff)
        expected_parent_text = TranslatedText.objects.get(
            reference=self.learning_unit_year.pk,
            text_label__label='resume',
            language=settings.LANGUAGE_CODE_FR
        )
        self.assertEqual(response.data['resume'], expected_parent_text.text)

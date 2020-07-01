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

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.business.education_groups.general_information_sections import DETAILED_PROGRAM, \
    SKILLS_AND_ACHIEVEMENTS, COMMON_DIDACTIC_PURPOSES
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.education_group_year import EducationGroupYearFactory, EducationGroupYearCommonFactory
from base.tests.factories.person import PersonFactory
from cms.enums.entity_name import OFFER_YEAR
from cms.tests.factories.translated_text import TranslatedTextFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.ddd.repositories import load_tree
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory
from webservices.api.serializers.general_information import GeneralInformationSerializer
from webservices.business import EVALUATION_KEY, SKILLS_AND_ACHIEVEMENTS_INTRO, SKILLS_AND_ACHIEVEMENTS_EXTRA


class GeneralInformationTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.language = settings.LANGUAGE_CODE_EN
        cls.egy = EducationGroupYearFactory(education_group_type__name=TrainingType.PGRM_MASTER_120.name)
        cls.group = GroupYearFactory(
            academic_year=cls.egy.academic_year,
            partial_acronym=cls.egy.partial_acronym,
            education_group_type__name=cls.egy.education_group_type.name
        )
        element = ElementFactory(group_year=cls.group)
        StandardEducationGroupVersionFactory(offer=cls.egy, root_group=cls.group)
        cls.node = load_tree.load(element.id).root_node
        common_egy = EducationGroupYearCommonFactory(academic_year=cls.egy.academic_year)
        cls.pertinent_sections = {
            'specific': [EVALUATION_KEY, DETAILED_PROGRAM, SKILLS_AND_ACHIEVEMENTS],
            'common': [COMMON_DIDACTIC_PURPOSES, EVALUATION_KEY]
        }
        for section in cls.pertinent_sections['common']:
            TranslatedTextLabelFactory(language=cls.language, text_label__label=section, text_label__entity=OFFER_YEAR)
            TranslatedTextFactory(
                reference=common_egy.id,
                entity=OFFER_YEAR,
                language=cls.language,
                text_label__label=section,
                text_label__entity=OFFER_YEAR
            )
        for section in cls.pertinent_sections['specific']:
            if section != EVALUATION_KEY:
                TranslatedTextLabelFactory(
                    language=cls.language,
                    text_label__label=section,
                    text_label__entity=OFFER_YEAR
                )
            TranslatedTextFactory(
                reference=cls.egy.id,
                entity=OFFER_YEAR,
                language=cls.language,
                text_label__label=section,
                text_label__entity=OFFER_YEAR
            )
        for label in [SKILLS_AND_ACHIEVEMENTS_INTRO, SKILLS_AND_ACHIEVEMENTS_EXTRA]:
            TranslatedTextFactory(
                text_label__label=label,
                reference=cls.egy.id,
                entity=OFFER_YEAR,
                language=cls.language,
                text_label__entity=OFFER_YEAR
            )
        cls.url = reverse('generalinformations_read', kwargs={
            'acronym': cls.egy.acronym,
            'year': cls.egy.academic_year.year,
            'language': cls.language
        })

    def setUp(self):
        sections_patcher = mock.patch(
            "base.business.education_groups.general_information_sections.SECTIONS_PER_OFFER_TYPE",
            {self.egy.education_group_type.name: self.pertinent_sections}
        )
        sections_patcher.start()
        self.addCleanup(sections_patcher.stop)
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

    def test_get_results_case_education_group_year_not_found(self):
        invalid_url = reverse('generalinformations_read', kwargs={
            'acronym': 'dummy',
            'year': 2019,
            'language': settings.LANGUAGE_CODE_EN
        })
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_results_based_on_egy_with_acronym(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = GeneralInformationSerializer(
            self.node, context={
                'language': self.language,
                'acronym': self.egy.acronym,
                'offer': self.egy
            }
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_results_based_on_egy_with_partial_acronym(self):
        url_partial_acronym = reverse('generalinformations_read', kwargs={
            'acronym': self.group.partial_acronym,
            'year': self.egy.academic_year.year,
            'language': self.language
        })

        response = self.client.get(url_partial_acronym)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = GeneralInformationSerializer(
            self.node, context={
                'language': self.language,
                'acronym': self.group.partial_acronym,
                'offer': self.egy
            }
        )
        self.assertEqual(response.data, serializer.data)

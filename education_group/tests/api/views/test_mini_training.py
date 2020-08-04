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
import urllib.parse

from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.models.enums import organization_type
from base.models.enums.education_group_types import MiniTrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import MiniTrainingFactory, TrainingFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from education_group.api.serializers.education_group_title import EducationGroupTitleSerializer
from education_group.api.serializers.mini_training import MiniTrainingDetailSerializer, MiniTrainingListSerializer
from education_group.api.views.mini_training import MiniTrainingList
from education_group.api.views.mini_training import OfferRoots
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory


class MiniTrainingTitleTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        anac = AcademicYearFactory()

        cls.egy = MiniTrainingFactory(academic_year=anac)
        cls.version = StandardEducationGroupVersionFactory(offer=cls.egy, is_transition=False)
        ElementFactory(group_year=cls.version.root_group)
        cls.person = PersonFactory()
        cls.url = reverse('education_group_api_v1:minitrainingstitle_read', kwargs={
            'official_partial_acronym': cls.version.offer.partial_acronym,
            'year': cls.version.root_group.academic_year.year
        })

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

    def test_get_results_case_education_group_year_not_found(self):
        invalid_url = reverse('education_group_api_v1:minitrainingstitle_read', kwargs={
            'official_partial_acronym': 'ACRO',
            'year': 2019
        })
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = EducationGroupTitleSerializer(self.version, context={'language': settings.LANGUAGE_CODE})
        self.assertEqual(response.data, serializer.data)


class MiniTrainingListTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.entity_version = EntityVersionFactory(entity__organization__type=organization_type.MAIN)

        cls.mini_trainings = []
        cls.versions = []
        for partial_acronym in ['LLOGO210O', 'NLOGO2101', 'WLOGO2102']:
            offer = MiniTrainingFactory(
                partial_acronym=partial_acronym,
                academic_year=cls.academic_year,
                management_entity=cls.entity_version.entity,
            )
            mini_training = GroupYearFactory(
                acronym=offer.acronym,
                partial_acronym=partial_acronym,
                academic_year=cls.academic_year,
                management_entity=cls.entity_version.entity,
                education_group_type=offer.education_group_type
            )

            cls.mini_trainings.append(mini_training)
            cls.versions.append(StandardEducationGroupVersionFactory(
                root_group=mini_training,
                offer=offer
            ))
        cls.user = UserFactory()
        cls.url = reverse('education_group_api_v1:' + MiniTrainingList.name)

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_filter_by_multiple_education_group_type(self):
        """
        This test ensure that multiple filtering by education_group_type will act as an OR
        """
        data = {
            'education_group_type': [mini_training.education_group_type.name for mini_training in self.mini_trainings]
        }

        response = self.client.get(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_get_filter_by_code(self):
        url = self.url + "?" + urllib.parse.urlencode({
            'code': self.versions[1].root_group.partial_acronym
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['code'], self.versions[1].root_group.partial_acronym)

    def test_get_filter_by_acronym(self):
        url = self.url + "?" + urllib.parse.urlencode({
            'acronym': self.mini_trainings[0].acronym
        })

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_filter_from_year_to_year(self):
        MiniTrainingFactory(academic_year__year=self.academic_year.year - 1)
        MiniTrainingFactory(academic_year__year=self.academic_year.year + 1)

        url = self.url + "?" + urllib.parse.urlencode({
            'from_year': self.academic_year.year,
            'to_year': self.academic_year.year
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_order_by_code_in_reverse(self):
        url = self.url + "?" + urllib.parse.urlencode({
            'ordering': '-code'
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['code'], self.versions[2].root_group.partial_acronym)
        self.assertEqual(response.data['results'][1]['code'], self.versions[1].root_group.partial_acronym)
        self.assertEqual(response.data['results'][2]['code'], self.versions[0].root_group.partial_acronym)

    def test_get_mini_training_case_filter_lowercase_acronym(self):
        query_string = {'partial_acronym': self.mini_trainings[1].partial_acronym.lower()}

        response = self.client.get(self.url, data=query_string)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = MiniTrainingListSerializer(
            self.versions[1],
            context={
                'request': RequestFactory().get(self.url, query_string),
                'language': settings.LANGUAGE_CODE_FR
            },
        )
        self.assertEqual(dict(response.data['results'][0]), serializer.data)

    def test_get_case_filter_campus(self):
        query_string = {'campus': self.mini_trainings[2].main_teaching_campus.name}

        response = self.client.get(self.url, data=query_string)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = MiniTrainingListSerializer(
            [self.versions[2]],
            many=True,
            context={'request': RequestFactory().get(self.url, query_string)},
        )
        self.assertEqual(response.data['results'], serializer.data)


class GetMiniTrainingTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.mini_training = MiniTrainingFactory(partial_acronym='LGENR100I', academic_year=cls.academic_year)
        cls.version = StandardEducationGroupVersionFactory(
            offer=cls.mini_training,
            root_group__academic_year=cls.academic_year,
            root_group__education_group_type=cls.mini_training.education_group_type,
            root_group__partial_acronym=cls.mini_training.partial_acronym
        )
        cls.user = UserFactory()
        cls.url = reverse('education_group_api_v1:mini_training_read', kwargs={
            'official_partial_acronym': cls.version.root_group.partial_acronym,
            'year': cls.academic_year.year
        })

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_valid_mini_training(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = MiniTrainingDetailSerializer(
            self.version,
            context={
                'request': RequestFactory().get(self.url),
                'language': settings.LANGUAGE_CODE_FR
            },
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid_mini_training_case_not_found(self):
        invalid_url = reverse('education_group_api_v1:mini_training_read', kwargs={
            'official_partial_acronym': 'ACRO',
            'year': 2033
        })
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OfferRootsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.entity_version = EntityVersionFactory(entity__organization__type=organization_type.MAIN)

        cls.minor = GroupYearFactory(
            academic_year=cls.academic_year,
            education_group_type__name=MiniTrainingType.OPEN_MINOR.name
        )
        minor_element = ElementFactory(group_year=cls.minor)
        for _ in range(0, 3):
            offer = TrainingFactory(academic_year=cls.academic_year)
            group = GroupYearFactory(
                academic_year=cls.academic_year,
                acronym=offer.acronym,
                partial_acronym=offer.partial_acronym,
                education_group_type=offer.education_group_type
            )
            StandardEducationGroupVersionFactory(offer=offer, root_group=group)
            GroupElementYearFactory(parent_element__group_year=group, child_element=minor_element)

        cls.user = UserFactory()
        cls.url = reverse('education_group_api_v1:' + OfferRoots.name, kwargs={
            'official_partial_acronym': cls.minor.partial_acronym,
            'year': cls.academic_year.year
        })

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

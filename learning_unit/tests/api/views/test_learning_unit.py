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
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.models.learning_unit_year import LearningUnitYear, LearningUnitYearQuerySet
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from learning_unit.api.serializers.learning_unit import LearningUnitDetailedSerializer, LearningUnitSerializer, \
    LearningUnitTitleSerializer, ExternalLearningUnitDetailedSerializer
from learning_unit.api.views.learning_unit import LearningUnitList


class LearningUnitListTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):

        cls.academic_years = GenerateAcademicYear(
            start_year=AcademicYearFactory(year=2015),
            end_year=AcademicYearFactory(year=2020)
        )

        cls.requirement_entity_version = EntityVersionFactory(
            start_date=cls.academic_years[0].start_date,
            end_date=cls.academic_years[-1].end_date,
        )

        cls.learning_unit_years = []
        for academic_year in cls.academic_years:
            cls.learning_unit_years.append(
                LearningUnitYearFactory(
                    academic_year=academic_year,
                    learning_container_year__academic_year=academic_year,
                    learning_container_year__requirement_entity=cls.requirement_entity_version.entity
                )
            )

        cls.person = PersonFactory()
        cls.url = reverse('learning_unit_api_v1:' + LearningUnitList.name)

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

    def test_get_all_training_ensure_response_have_next_previous_results_count(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue('previous' in response.data)
        self.assertTrue('next' in response.data)
        self.assertTrue('results' in response.data)

        self.assertTrue('count' in response.data)
        expected_count = LearningUnitYear.objects.all().count()
        self.assertEqual(response.data['count'], expected_count)

    def test_get_results_without_filtering(self):
        response = self.client.get(self.url, {'lang': 'fr'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        qs = LearningUnitYear.objects.all().annotate_full_title().order_by('-academic_year__year', 'acronym')
        serializer = LearningUnitSerializer(
            qs,
            many=True,
            context={
                'request': RequestFactory().get(self.url),
                'language': settings.LANGUAGE_CODE
            }
        )
        self.assertEqual(response.data['results'], serializer.data)

    def test_get_only_learning_unit_with_container(self):
        LearningUnitYearFactory(learning_container_year=None)
        response = self.client.get(self.url, {'lang': 'fr'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        qs = LearningUnitYear.objects.filter(
            learning_container_year__isnull=False
        ).annotate_full_title().order_by('-academic_year__year', 'acronym')
        serializer = LearningUnitSerializer(
            qs,
            many=True,
            context={
                'request': RequestFactory().get(self.url),
                'language': settings.LANGUAGE_CODE
            }
        )
        self.assertEqual(response.data['results'], serializer.data)

    def test_get_results_filter_by_academic_year(self):
        response = self.client.get(self.url, data={'year': self.academic_years[3].year})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        qs = LearningUnitYear.objects.filter(
            pk=self.learning_unit_years[3].pk
        ).annotate_full_title().order_by('-academic_year__year', 'acronym')

        serializer = LearningUnitSerializer(
            qs,
            many=True,
            context={
                'request': RequestFactory().get(self.url),
                'language': settings.LANGUAGE_CODE
            }
        )
        self.assertEqual(response.data['results'], serializer.data)

    def test_get_results_filter_by_acronym_exact_match(self):
        expected_learning_unit_year = self.learning_unit_years[2]

        response = self.client.get(self.url, data={'acronym': expected_learning_unit_year.acronym})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        qs = LearningUnitYear.objects.filter(
            pk=expected_learning_unit_year.pk
        ).annotate_full_title().order_by('-academic_year__year', 'acronym')

        serializer = LearningUnitSerializer(
            qs,
            many=True,
            context={
                'request': RequestFactory().get(self.url),
                'language': settings.LANGUAGE_CODE
            }
        )
        self.assertEqual(response.data['results'], serializer.data)

    def test_get_results_filter_by_campus(self):
        response = self.client.get(self.url, data={'campus': self.learning_unit_years[2].campus.name})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        qs = LearningUnitYear.objects.filter(
            pk=self.learning_unit_years[2].pk
        ).annotate_full_title().order_by('-academic_year__year', 'acronym')

        serializer = LearningUnitSerializer(
            qs,
            many=True,
            context={
                'request': RequestFactory().get(self.url),
                'language': settings.LANGUAGE_CODE
            }
        )
        self.assertEqual(response.data['results'], serializer.data)


class LearningUnitDetailedTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        anac = AcademicYearFactory()
        requirement_entity = EntityFactory()
        EntityVersionFactory(
            start_date=AcademicYearFactory(year=anac.year - 1).start_date,
            end_date=AcademicYearFactory(year=anac.year + 1).end_date,
            entity=requirement_entity
        )
        cls.luy = LearningUnitYearFactory(
            academic_year=anac,
            learning_container_year__requirement_entity=requirement_entity
        )
        cls.person = PersonFactory()
        url_kwargs = {
            'acronym': cls.luy.acronym,
            'year': cls.luy.academic_year.year
        }
        cls.url = reverse('learning_unit_api_v1:learningunits_read', kwargs=url_kwargs)

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
            'learning_unit_api_v1:learningunits_read',
            kwargs={'acronym': 'ACRO', 'year': 2019}
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        luy_with_full_title = LearningUnitYear.objects.filter(pk=self.luy.pk).annotate_full_title()
        luy_with_full_title = LearningUnitYearQuerySet.annotate_entities_allocation_and_requirement_acronym(
            luy_with_full_title
        ).get()
        serializer = LearningUnitDetailedSerializer(
            luy_with_full_title,
            context={
                'request': RequestFactory().get(self.url),
                'language': settings.LANGUAGE_CODE
            }
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_results_external_ue(self):
        ExternalLearningUnitYearFactory(learning_unit_year=self.luy)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        luy_with_full_title = LearningUnitYear.objects.filter(pk=self.luy.pk).annotate_full_title()
        luy_with_full_title = LearningUnitYearQuerySet.annotate_entities_allocation_and_requirement_acronym(
            luy_with_full_title
        ).get()
        serializer = ExternalLearningUnitDetailedSerializer(
            luy_with_full_title,
            context={
                'request': RequestFactory().get(self.url),
                'language': settings.LANGUAGE_CODE
            }
        )
        self.assertEqual(response.data, serializer.data)


class LearningUnitTitleTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        anac = AcademicYearFactory()

        cls.luy = LearningUnitYearFactory(
            academic_year=anac,
        )
        cls.person = PersonFactory()
        cls.url = reverse('learning_unit_api_v1:learningunitstitle_read', kwargs={
            'acronym': cls.luy.acronym,
            'year': cls.luy.academic_year.year
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

    def test_get_results_case_learning_unit_year_not_found(self):
        invalid_url = reverse('learning_unit_api_v1:learningunitstitle_read', kwargs={
            'acronym': 'ACRO',
            'year': 2019
        })
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        luy_with_full_title = LearningUnitYear.objects.filter(pk=self.luy.pk).annotate_full_title().get()
        serializer = LearningUnitTitleSerializer(luy_with_full_title, context={'language': settings.LANGUAGE_CODE})
        self.assertEqual(response.data, serializer.data)

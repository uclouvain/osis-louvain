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

from django.db.models import F
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from attribution.models.attribution_charge_new import AttributionChargeNew
from attribution.tests.factories.attribution import AttributionNewFactory
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory
from learning_unit.api.serializers.attribution import LearningUnitAttributionSerializer


class LearningUnitAttributionTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        tutor = TutorFactory(person=PersonFactory())
        attribution = AttributionNewFactory(
            tutor=tutor,
            substitute=PersonFactory()
        )
        cls.luy = LearningUnitYearFactory()
        cls.attrib = AttributionChargeNewFactory(
            attribution=attribution,
            learning_component_year__learning_unit_year=cls.luy
        )

        cls.person = PersonFactory()
        url_kwargs = {
            'acronym': cls.luy.acronym,
            'year': cls.luy.academic_year.year
        }
        cls.url = reverse('learning_unit_api_v1:learningunitattributions_read', kwargs=url_kwargs)

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
            'learning_unit_api_v1:learningunitattributions_read',
            kwargs={'acronym': 'ACRO', 'year': 2019}
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attribution = AttributionChargeNew.objects.annotate(
            first_name=F('attribution__tutor__person__first_name'),
            middle_name=F('attribution__tutor__person__middle_name'),
            last_name=F('attribution__tutor__person__last_name'),
            email=F('attribution__tutor__person__email'),
            global_id=F('attribution__tutor__person__global_id'),
        ).get(id=self.attrib.id)

        serializer = LearningUnitAttributionSerializer([attribution], many=True)
        self.assertEqual(response.data, serializer.data)

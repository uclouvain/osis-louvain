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
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.api.models.program_manager_check import CheckAccessToStudent
from base.api.serializers.program_manager_check import CheckAccessToStudentSerializer
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.user import UserFactory


class GetPersonRolesTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory(global_id='123456')
        cls.student_1 = StudentFactory(registration_id='123456')
        cls.student_2 = StudentFactory(registration_id='654321')
        cls.offer_year_1 = OfferYearFactory()
        cls.offer_year_2 = OfferYearFactory()
        cls.offer_enrollment_1 = OfferEnrollmentFactory(offer_year=cls.offer_year_1, student=cls.student_1)
        cls.offer_enrollment_2 = OfferEnrollmentFactory(offer_year=cls.offer_year_2, student=cls.student_2)
        cls.program_manager = ProgramManagerFactory(person=cls.person, offer_year=cls.offer_year_1)
        cls.url = reverse('base_api_v1:check-program-manager', kwargs={'global_id': cls.person.global_id,
                                                                       'registration_id': cls.student_1.registration_id})

        cls.user = UserFactory()

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put']
        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_manager_access_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expectedResponse = CheckAccessToStudent(self.person.global_id, self.student_1.registration_id, True)
        serializer = CheckAccessToStudentSerializer(
            expectedResponse,
            context={'request': RequestFactory().get(self.url)},
        )
        self.assertEqual(response.data, serializer.data)

    def test_manager_access_denied(self):
        self.url = reverse('base_api_v1:check-program-manager',
                           kwargs={'global_id': self.person.global_id,
                                   'registration_id': self.student_2.registration_id})
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expectedResponse = CheckAccessToStudent(self.person.global_id, self.student_2.registration_id, False)
        serializer = CheckAccessToStudentSerializer(
            expectedResponse,
            context={'request': RequestFactory().get(self.url)},
        )
        self.assertEqual(response.data, serializer.data)
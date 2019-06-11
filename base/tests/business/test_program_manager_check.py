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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase

from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.student import StudentFactory

from base.business.program_manager import program_manager_check as pm_business


class CheckAccessToStudentTestCase(TestCase):

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

    def testManagerAllowed(self):
        self.assertTrue(pm_business.check_access_to_student(self.person.global_id, self.student_1.registration_id))

    def testManagerNotAllowed(self):
        self.assertFalse(pm_business.check_access_to_student(self.person.global_id, self.student_2.registration_id))
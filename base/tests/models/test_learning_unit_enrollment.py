##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from django.test import TestCase
from base.models import learning_unit_enrollment
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollment
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


def create_learning_unit_enrollment(learning_unit_year, offer_enrollment):
    return LearningUnitEnrollment(learning_unit_year=learning_unit_year,
                                   offer_enrollment=offer_enrollment)


class LearningUnitEnrollmentTest(TestCase):
    def setUp(self):
        academic_year = AcademicYearFactory(year=datetime.datetime.now().year)
        offer_year = OfferYearFactory(academic_year=academic_year)
        student_1 = StudentFactory(person=PersonFactory(last_name='Durant', first_name='Thomas'))
        student_2 = StudentFactory(person=PersonFactory(last_name='Dupont', first_name='Raph'))
        student_3 = StudentFactory(person=PersonFactory(last_name='Duclou', first_name='Paul'))
        offer_enrollement_1 = OfferEnrollmentFactory(offer_year=offer_year,student=student_1)
        offer_enrollement_2 = OfferEnrollmentFactory(offer_year=offer_year, student=student_2)
        offer_enrollement_3 = OfferEnrollmentFactory(offer_year=offer_year,student=student_3)
        self.l_unit_year = LearningUnitYearFactory(academic_year=academic_year)
        LearningUnitEnrollment(learning_unit_year=self.l_unit_year, offer_enrollment=offer_enrollement_1)
        LearningUnitEnrollment(learning_unit_year=self.l_unit_year, offer_enrollment=offer_enrollement_2)
        LearningUnitEnrollment(learning_unit_year=self.l_unit_year, offer_enrollment=offer_enrollement_3)

    def test_find_by_learningunit_enrollment_order_by_last_name_first_name(self):
        request = learning_unit_enrollment.find_by_learningunit_enrollment(self.l_unit_year)
        self.assertEqual(len(request), 3)
        self.assertEqual(request[0].student.person.last_name, "Duclou")
        self.assertEqual(request[1].student.person.last_name, "Dupont")
        self.assertEqual(request[2].student.person.last_name, "Durant")

    def test_find_by_learningunit_enrollement_bad_value(self):
        with self.assertRaises(ValueError):
            learning_unit_enrollment.find_by_learningunit_enrollment("BAD VALUE")
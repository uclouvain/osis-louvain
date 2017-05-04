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
from django.test import TestCase
from base.tests.models import test_student
from internship.models import internship_student_information
from internship.models.internship_student_information import InternshipStudentInformation
from internship.tests.factories.cohort import CohortFactory


def create_student_information(person, contest="GENERALIST", cohort=None):
    if cohort is None:
        cohort = CohortFactory()

    return InternshipStudentInformation.objects.create(
        person=person, location="location", postal_code="00", city="city",
        country="country", contest=contest, cohort=cohort
    )


class TestStudentInformation(TestCase):
    def setUp(self):
        self.cohort = CohortFactory()
        student_1 = test_student.create_student("first", "last", "01")
        student_2 = test_student.create_student("first", "last", "02")
        student_3 = test_student.create_student("first", "last", "03")
        student_4 = test_student.create_student("first", "last", "04")

        contest_generalist = "GENERALIST"
        contest_specialist = "SPECIALIST"

        create_student_information(student_1.person, contest_generalist, cohort=self.cohort)
        create_student_information(student_2.person, contest_generalist, cohort=self.cohort)
        create_student_information(student_3.person, contest_generalist, cohort=self.cohort)
        create_student_information(student_4.person, contest_specialist, cohort=self.cohort)

    def test_get_number_of_specialists(self):
        expected = 1
        actual = internship_student_information.get_number_of_specialists(self.cohort)
        self.assertEqual(expected, actual)

    def test_get_number_of_generalists(self):
        expected = 3
        actual = internship_student_information.get_number_of_generalists(self.cohort)
        self.assertEqual(expected, actual)

    def test_get_number_students(self):
        expected = 4
        actual = internship_student_information.get_number_students(self.cohort)
        self.assertEqual(expected, actual)












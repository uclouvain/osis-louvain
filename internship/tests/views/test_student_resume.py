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
from django.contrib.auth.models import Permission, User
from django.core.urlresolvers import resolve, reverse
from django.test import TestCase

from internship.tests.factories.cohort import CohortFactory
from internship.tests.models import test_organization, test_internship_speciality, test_internship_choice, \
    test_internship_student_information
from base.tests.models import test_student
from internship.views import student_resume
from internship.tests.factories.cohort import CohortFactory
from internship.tests.factories.internship import InternshipFactory


class TestStudentResume(TestCase):
    def setUp(self):
        self.cohort = CohortFactory()
        organization = test_organization.create_organization(cohort=self.cohort)
        self.student_1 = test_student.create_student(first_name="first", last_name="last", registration_id="64641200")
        self.student_2 = test_student.create_student(first_name="first", last_name="last", registration_id="606012")
        speciality = test_internship_speciality.create_speciality(cohort=self.cohort)

        self.internship = InternshipFactory(cohort=self.cohort)
        self.internship_2 = InternshipFactory(cohort=self.cohort)
        self.internship_3 = InternshipFactory(cohort=self.cohort)
        self.internship_4 = InternshipFactory(cohort=self.cohort)

        self.choice_1 = test_internship_choice.create_internship_choice(organization, self.student_1, speciality,
                                                                        internship=self.internship)
        self.choice_2 = test_internship_choice.create_internship_choice(organization, self.student_1, speciality,
                                                                        internship=self.internship_2)
        self.choice_3 = test_internship_choice.create_internship_choice(organization, self.student_1, speciality,
                                                                        internship=self.internship_3)
        self.choice_4 = test_internship_choice.create_internship_choice(organization, self.student_1, speciality,
                                                                        internship=self.internship_4)

        self.choice_5 = test_internship_choice.create_internship_choice(organization, self.student_2, speciality,
                                                                        internship=self.internship)
        self.choice_6 = test_internship_choice.create_internship_choice(organization, self.student_2, speciality,
                                                                        internship=self.internship_2)
        self.choice_7 = test_internship_choice.create_internship_choice(organization, self.student_2, speciality,
                                                                        internship=self.internship_3)

    def test_get_students_status(self):
        expected = []
        actual = student_resume.get_students_with_status(cohort=self.cohort)
        self.assertCountEqual(expected, actual)

        test_internship_student_information.create_student_information(self.student_1.person, "GENERALIST", cohort=self.cohort)
        test_internship_student_information.create_student_information(self.student_2.person, "GENERALIST", cohort=self.cohort)
        expected = [(self.student_1, True), (self.student_2, False)]
        actual = student_resume.get_students_with_status(cohort=self.cohort)
        self.assertCountEqual(expected, actual)
        for item_expected in expected:
            self.assertIn(item_expected, actual)



class StudentResumeViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('demo', 'demo@demo.org', 'passtest')
        permission = Permission.objects.get(codename='is_internship_manager')
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

        self.cohort = CohortFactory()

    def test_internships_student_resume(self):
        from internship.views.student_resume import internships_student_resume
        url = reverse(internships_student_resume, kwargs={
            'cohort_id': self.cohort.id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)




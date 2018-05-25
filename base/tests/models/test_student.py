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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase
from base.models import student
from base.tests.models import test_person
from base.tests.factories.person import PersonFactory, PersonWithoutUserFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.offer import OfferFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory


def create_student(first_name, last_name, registration_id):
    person = test_person.create_person(first_name, last_name)
    a_student = student.Student(person=person, registration_id=registration_id)
    a_student.save()
    return a_student


class StudentTest(TestCase):
    def test_find_by_with_person_first_name_case_insensitive(self):
        a_person = PersonWithoutUserFactory.create(first_name="John")
        a_student = StudentFactory.create(person=a_person)
        found = list(student.find_by(person_first_name="john"))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].id, a_student.id)

    def test_find_by_with_person_last_name_case_insensitive(self):
        a_person = PersonWithoutUserFactory.create(last_name="Smith")
        a_student = StudentFactory.create(person=a_person)
        found = list(student.find_by(person_name="smith"))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].id, a_student.id)

    def test_find_by_with_registration_id(self):
        tmp_student = StudentFactory()
        db_student = list(student.find_by(registration_id=tmp_student.registration_id, full_registration=False))[0]
        self.assertIsNotNone(db_student)
        self.assertEqual(db_student.registration_id, tmp_student.registration_id)

    def test_find_by_with_full_registration_id(self):
        tmp_student = StudentFactory()
        db_student = list(student.find_by(registration_id=tmp_student.registration_id, full_registration=True))[0]
        self.assertIsNotNone(db_student)
        self.assertEqual(db_student.registration_id, tmp_student.registration_id)

    def test_find_by_with_username(self):
        tmp_student = StudentFactory()
        db_student = list(student.find_by(person_username=tmp_student.person.user))[0]
        self.assertIsNotNone(db_student)
        self.assertEqual(db_student, tmp_student)

    def test_find_by_id(self):
        tmp_student = StudentFactory()
        db_student = student.find_by_id(tmp_student.id)
        self.assertIsNotNone(db_student)
        self.assertEqual(db_student, tmp_student)

    def test_find_by_offer(self):
        tmp_student = StudentFactory()
        tmp_offer_year = OfferYearFactory()
        OfferEnrollmentFactory.create(offer_year=tmp_offer_year, student=tmp_student)
        db_student = list(student.find_by_offer([tmp_offer_year.offer]))[0]
        self.assertIsNotNone(db_student)
        self.assertEqual(db_student, tmp_student)

    def test_find_by_offer_year(self):
        tmp_student = StudentFactory()
        tmp_offer_year = OfferYearFactory()
        OfferEnrollmentFactory.create(offer_year=tmp_offer_year, student=tmp_student)
        db_student = list(student.find_by_offer_year([tmp_offer_year][0]))[0]
        self.assertIsNotNone(db_student)
        self.assertEqual(db_student, tmp_student)

    def test_find_by_person(self):
        tmp_student = StudentFactory()
        db_student = student.find_by_person(tmp_student.person)
        self.assertIsNotNone(db_student)
        self.assertEqual(db_student, tmp_student)

    def test_find_by_registration_id(self):
        tmp_student = StudentFactory()
        db_student = student.find_by_registration_id(tmp_student.registration_id)
        self.assertIsNotNone(db_student)
        self.assertEqual(db_student, tmp_student)

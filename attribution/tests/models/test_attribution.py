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
from django.contrib.auth.models import User
from base.tests.models import test_academic_year, test_learning_unit_year, test_tutor, test_person
from attribution.models import attribution


def create_attribution(tutor, learning_unit_year, score_responsible=False):
    an_attribution = attribution.Attribution(tutor=tutor, learning_unit_year=learning_unit_year,
                                             score_responsible=score_responsible)
    an_attribution.save()
    return an_attribution


class AttributionTest(TestCase):

    def test_find_responsible(self):
        academic_year = test_academic_year.create_academic_year()
        learning_unit_year = test_learning_unit_year.create_learning_unit_year('LDROI', 'Droit', academic_year)
        first_coordinator = test_tutor.create_tutor(first_name="Jane", last_name="Phonda")
        second_coordinator = test_tutor.create_tutor(first_name="Marie", last_name="Jane")
        third_coordinator = test_tutor.create_tutor(first_name="John", last_name="Smith")
        teacher = test_tutor.create_tutor(first_name="Joseph", last_name="Miller")

        create_attribution(first_coordinator, learning_unit_year, True)
        create_attribution(second_coordinator, learning_unit_year, True)
        third_attribution = create_attribution(third_coordinator, learning_unit_year, True)
        create_attribution(teacher, learning_unit_year)

        responsible = attribution.find_responsible(learning_unit_year)

        self.assertEqual(responsible.person.first_name, third_attribution.tutor.person.first_name)

    def test_find_responsible_without_attribution(self):
        academic_year = test_academic_year.create_academic_year()
        learning_unit_year = test_learning_unit_year.create_learning_unit_year('LDROI', 'Droit', academic_year)
        self.assertIsNone(attribution.find_responsible(learning_unit_year))

    def test_find_responsible_without_resposible(self):
        academic_year = test_academic_year.create_academic_year()
        learning_unit_year = test_learning_unit_year.create_learning_unit_year('LDROI', 'Droit', academic_year)
        first_teacher = test_tutor.create_tutor(first_name="John", last_name="Smith")
        second_teacher = test_tutor.create_tutor(first_name="Marie", last_name="Jane")

        create_attribution(first_teacher, learning_unit_year)
        create_attribution(second_teacher, learning_unit_year)

        self.assertIsNone(attribution.find_responsible(learning_unit_year))

    def test_is_score_responsible(self):
        academic_year = test_academic_year.create_academic_year()
        learning_unit_year = test_learning_unit_year.create_learning_unit_year('LDROI', 'Droit', academic_year)

        user = User(first_name="John", last_name="Smith")
        user.save()
        person = test_person.create_person_with_user(user)
        tutor = test_tutor.create_tutor_with_person(person)
        create_attribution(tutor, learning_unit_year, True)

        self.assertTrue(attribution.is_score_responsible(user, learning_unit_year))

    def test_is_score_responsible_without_attribution(self):
        academic_year = test_academic_year.create_academic_year()
        learning_unit_year = test_learning_unit_year.create_learning_unit_year('LDROI', 'Droit', academic_year)

        user = User()

        self.assertFalse(attribution.is_score_responsible(user, learning_unit_year))

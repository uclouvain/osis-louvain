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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

import base.models.student as student
import scripts.populate_utility as util
import scripts.populate_base_person as person_util


def create_student_and_person():
    """
    Creates a student and the person associated to it
    and saves it.
    :return: a student object.
    """
    p = person_util.create_person()

    return create_student(p)


def create_student_and_person_and_user():
    """
    Creates a student and also the person and user associated to
    that student. The student is saved.
    :return: a student object
    """
    p = person_util.create_person_and_user()

    return create_student(p)


def create_student(p):
    """
    Create a student
    :param p: a person object
    :return: a student object
    """
    external_id = p.external_id
    registration_id = util.random_id()

    s = student.Student(person=p, external_id=external_id,
                        registration_id=registration_id)
    s.save()
    return s


def create_students(number=20):
    """
    Creates multiple students and saves them.
    The associated persons are created
    :param number: number of students to create.
    :return: a list of students
    """
    list_students = []

    for i in range(0, number):
        s = create_student_and_person()
        list_students.append(s)

    return list_students


def creates_persons_and_users(number=20):
    """
    Creates multiple students with the associated users and persons
    and saves them.
    :param number: number of students to create.
    :return: a list of students
    """
    list_students = []

    for i in range(0, number):
        s = create_student_and_person_and_user()
        list_students.append(s)

    return list_students

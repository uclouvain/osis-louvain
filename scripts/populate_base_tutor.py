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

import base.models.tutor as tutor
import scripts.populate_base_person as person_util


def create_tutor_and_person():
    """
    Creates a tutor and the person associated to it
    and saves it.
    :return: a tutor object.
    """
    p = person_util.create_person()

    return create_tutor(p)


def create_tutor_and_person_and_user():
    """
    Creates a tutor and also the person and user associated to
    that tutor. The tutor is saved.
    :return: a tutor object
    """
    p = person_util.create_person_and_user()

    return create_tutor(p)


def create_tutor(p):
    """
    Create a tutor
    :param p: a person object
    :return: a tutor object
    """
    external_id = p.external_id

    t = tutor.Tutor(person=p, external_id=external_id)
    t.save()
    return t


def create_tutors(number=20):
    """
    Creates multiple tutors and saves them.
    The associated persons are created
    :param number: number of tutors to create.
    :return: a list of tutors
    """
    list_tutors = []

    for i in range(0, number):
        t = create_tutor_and_person()
        list_tutors.append(t)

    return list_tutors


def creates_persons_and_users(number=20):
    """
    Creates multiple tutors with the associated users and persons
    and saves them.
    :param number: number of tutors to create.
    :return: a list of tutors
    """
    list_tutors = []

    for i in range(0, number):
        t = create_tutor_and_person_and_user()
        list_tutors.append(t)

    return list_tutors

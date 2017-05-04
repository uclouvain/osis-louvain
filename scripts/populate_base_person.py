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

import base.models.person as person
import scripts.populate_utility as util
import scripts.populate_users as user_util


def create_person():
    """
    Creates a person and saves it.
    :return: a person object.
    """
    external_id = util.random_id()
    global_id = util.random_id()
    gender = util.random_gender()
    national_id = util.random_id()
    first_name = util.random_first_name(gender)
    last_name = util.random_last_name()
    email = util.email_based_on_names(first_name, last_name)

    p = person.Person(external_id=external_id, global_id=global_id,
                      gender=gender, national_id=national_id,
                      first_name=first_name, last_name=last_name,
                      email=email)
    p.save()

    return p


def create_person_and_user():
    """
    Creates a person and also the a user associated to
    that person. The person is saved.
    :return: a person object
    """
    p = create_person()
    user = user_util.create_user(p.first_name, p.last_name)
    user.email = p.email
    user.save()
    p.user = user
    p.save()
    return p


def create_persons(number=20):
    """
    Creates multiple persons and saves them.
    :param number: number of persons to create.
    :return: a list of persons
    """
    list_persons = []

    for i in range(0, number):
        p = create_person()
        list_persons.append(p)

    return list_persons


def creates_persons_and_users(number=20):
    """
    Creates multiple persons with the associated users and saves them.
    :param number: number of persons to create.
    :return: a list of persons
    """
    list_persons = []

    for i in range(0, number):
        p = create_person_and_user()
        list_persons.append(p)

    return list_persons

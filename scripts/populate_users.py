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

from django.contrib.auth.models import User
import scripts.populate_utility as utility


def create_user(first_name=None, last_name=None):
    """
    Creates a user and saves it.
    :param: first_name: first name of the user (string)
    :param: last_name: last name of the user (string)
    :return: a user object
    """
    username = utility.random_string()
    password = utility.random_password()
    email = utility.email_based_on_username(username)
    user = User.objects.create_user(username=username, password=password,
                                    email=email, first_name=first_name,
                                    last_name=last_name)
    user.save()
    return user


def create_users(number=20):
    """
    Creates users and saves them.
    :param number: number of users to create (int)
    :return: a list of users
    """
    list_users = []

    for i in range(0, number):
        user = create_user()
        list_users.append(user)

    return list_users

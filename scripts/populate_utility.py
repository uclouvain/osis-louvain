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

import linecache
import random
import string

path_dir_ressources = "scripts/ressources/"


def random_gender():
    """
    Returns a random gender (male or female).
    :return: a string representation of the gender ("M" of "F")
    """
    # Choose the gender
    gender = "M" if random.randint(0, 1) == 0 else "F"
    return gender


def random_first_name(gender):
    """
    Return a first name based on the gender.
    :param gender: a string representation of the gender ('M' or 'F')
    :return: a string
    """
    if gender == "M":
        file_path = path_dir_ressources+'male_first_names.txt'
    else:
        file_path = path_dir_ressources + 'female_first_names.txt'

    first_name = random_file_line(file_path).strip()

    return first_name


def random_last_name():
    """
    Returns a last_name.
    :return: a string
    """
    file_path = path_dir_ressources + "last_names.txt"
    last_name = random_file_line(file_path).strip()

    return last_name


def random_file_line(file_path):
    """
    Returns a random line of a file.
    The file must contains for first line the number of lines of the file.
    :param file_path: a string
    :return: a string
    """
    a = 2   # Because the line 1 indicates the number of lines of the file.
    b = int(linecache.getline(file_path, 1))
    random_line = linecache.getline(file_path, random.randint(a, b))
    return random_line


def random_number(minimum, maximum):
    """
    Returns a random number comprised in the interval [minimum, maximum].
    :param minimum: an int
    :param maximum: an int
    :return: an int
    """
    return random.randint(minimum, maximum)


def fixed_password():
    """
    Returns a fixed password.
    :return: a string
    """
    password = "testpassword"
    return password


def random_password(length=8):
    """
    Returns a random password.
    :param length: length of the password (default = 8).
    :return: a string
    """
    return random_string(length)


def random_string(length=8):
    """
    Return a random string
    :param length of the string (default = 8).
    :return: a string
    """
    s = ""
    for i in range(0, length):
        s += random_letter_digit()

    return s


def random_letter_digit():
    """
    Returns a random letter or digit.
    :return: a character (letter or digit)
    """
    choices = string.ascii_letters + string.digits
    return random.choice(choices)


def random_email(length=10, suffix="@test.com"):
    """
    Return a random email.
    :param length: length of the email username.
    :param suffix: suffix of the email
    :return: a string
    """
    return random_string(length) + suffix


def email_based_on_names(first_name, last_name, suffix="@test.com"):
    """
    Returns an email of the form: "first_name.last_name@test.com"
    :param first_name: a string
    :param last_name: a string
    :param suffix: a string
    :return: a string
    """
    return first_name + "." + last_name + suffix


def email_based_on_username(username, suffix="@test.com"):
    """
    Returns an email of the form "username@test.com"
    :param username: a string
    :param suffix: a string
    :return: a string
    """
    return username + suffix


def random_id(length=10):
    """
    Generates a random id comprised of only digits.
    :param length: lenght of th eid
    :return: a string
    """
    id = ""

    for i in range(0, length):
        id += str(random_number(0, 9))

    return id

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
from django.contrib.auth.models import User
from base.models.person import Person
from dissertation.models.adviser import Adviser


def create_adviser(person, type="PRF"):
    adv = Adviser.objects.create(person=person, type=type)
    return adv


def create_adviser_from_user(user, type="PRF"):
    person = Person.objects.create(user=user, first_name=user.username, last_name=user.username)
    return create_adviser(person, type)


def create_adviser_from_scratch(username, email, password, type="PRF"):
    user = User.objects.create_user(username=username, email=email, password=password)
    return create_adviser_from_user(user, type)

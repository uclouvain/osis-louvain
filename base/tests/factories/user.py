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
import datetime

import factory

from osis_common.utils.datetime import get_tzinfo


def generate_email(user, domain=None):
    if domain is None:
        domain = factory.Faker('domain_name').generate({})
    return '{0.first_name}.{0.last_name}@{1}'.format(user, domain).lower()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'auth.User'
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: 'username_{}'.format(n))
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(generate_email)
    password = factory.PostGenerationMethodCall('set_password', 'password123')

    is_active = True
    is_staff = False
    is_superuser = False

    last_login = factory.LazyAttribute(lambda _o: datetime.datetime(2000, 1, 1, tzinfo=get_tzinfo()))
    date_joined = factory.LazyAttribute(lambda _o: datetime.datetime(1999, 1, 1, tzinfo=get_tzinfo()))


class SuperUserFactory(UserFactory):
    username = factory.Sequence(lambda n: 'superusername_{0}'.format(n))
    is_superuser = True
    is_staff = True
    is_active = True

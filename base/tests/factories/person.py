##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import operator

import factory
import factory.fuzzy
from django.conf import settings
from django.contrib.auth.models import Group, Permission

from base import models as mdl
from base.models.enums.groups import CENTRAL_MANAGER_GROUP, FACULTY_MANAGER_GROUP, SIC_GROUP, UE_FACULTY_MANAGER_GROUP, \
    ADMINISTRATIVE_MANAGER_GROUP
from base.tests.factories.user import UserFactory


def generate_person_email(person, domain=None):
    if domain is None:
        domain = factory.Faker('domain_name').generate({})
    return '{0.first_name}.{0.last_name}@{1}'.format(person, domain).lower()


class PersonFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'base.Person'
        django_get_or_create = ('user',)  # One-to-one field

    first_name = factory.LazyAttribute(lambda person:
                                       person.user.first_name if person.user else factory.Faker('first_name'))
    last_name = factory.LazyAttribute(lambda person:
                                      person.user.last_name if person.user else factory.Faker('last_name'))

    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2016, 1, 1))
    email = factory.LazyAttribute(lambda person: person.user.email if person.user else '')
    phone = factory.Faker('phone_number')
    language = factory.Iterator(settings.LANGUAGES, getter=operator.itemgetter(0))
    gender = factory.Iterator(mdl.person.Person.GENDER_CHOICES, getter=operator.itemgetter(0))
    user = factory.SubFactory(UserFactory)
    global_id = None


class PersonWithoutUserFactory(PersonFactory):
    user = None
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(generate_person_email)


class PersonWithPermissionsFactory:
    def __init__(self, *permissions, groups=None, **kwargs):
        perms_obj = [Permission.objects.get_or_create(defaults={"name": p}, codename=p)[0] for p in permissions]
        self.person = PersonFactory(**kwargs)
        self.person.user.user_permissions.add(*perms_obj)

        if groups:
            add_person_to_groups(self.person, groups)

    def __new__(cls, *permissions, **kwargs):
        obj = super().__new__(cls)
        obj.__init__(*permissions, **kwargs)
        return obj.person


class FacultyManagerFactory(PersonWithPermissionsFactory):
    def __init__(self, *permissions, **kwargs):
        super().__init__(*permissions, groups=(FACULTY_MANAGER_GROUP, ), **kwargs)


class UEFacultyManagerFactory(PersonWithPermissionsFactory):
    def __init__(self, *permissions, **kwargs):
        super().__init__(*permissions, groups=(UE_FACULTY_MANAGER_GROUP, ), **kwargs)


class CentralManagerFactory(PersonWithPermissionsFactory):
    def __init__(self, *permissions, **kwargs):
        super().__init__(*permissions, groups=(CENTRAL_MANAGER_GROUP, ), **kwargs)


class SICFactory(PersonWithPermissionsFactory):
    def __init__(self, *permissions, **kwargs):
        super().__init__(*permissions, groups=(SIC_GROUP, ), **kwargs)


class AdministrativeManagerFactory(PersonWithPermissionsFactory):
    def __init__(self, *permissions, **kwargs):
        super().__init__(*permissions, groups=(ADMINISTRATIVE_MANAGER_GROUP, ), **kwargs)


def add_person_to_groups(person, groups):
    groups_obj = [Group.objects.get_or_create(name=name)[0] for name in groups]
    person.user.groups.add(*groups_obj)

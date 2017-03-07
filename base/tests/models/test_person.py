##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
import functools
import contextlib

import factory

from django.test import TestCase
from django.test import override_settings

from base.models import person
from base.enums import person_source_type
from base.factories.person import PersonFactory, generate_person_email


def create_person(first_name, last_name, email=None):
    a_person = person.Person(first_name=first_name, last_name=last_name, email=email)
    a_person.save()
    return a_person


def create_person_with_user(user):
    a_person = person.Person(first_name=user.first_name, last_name=user.last_name, user=user)
    a_person.save()
    return a_person


class PersonTestCase(TestCase):
    @contextlib.contextmanager
    def assertDontRaises(self):
        try:
            yield
        except AttributeError:
            self.fail('Exception not excepted')


class PersonTest(PersonTestCase):
    def test_find_by_id(self):
        tmp_person = PersonFactory()
        db_person = person.find_by_id(tmp_person.id)
        self.assertIsNotNone(tmp_person.user)
        self.assertEqual(db_person.id, tmp_person.id)
        self.assertEqual(db_person.email, tmp_person.email)

    @override_settings(INTERNAL_EMAIL_SUFIX='osis.org')
    def test_person_from_extern_source(self):
        person_email = functools.partial(generate_person_email, domain='osis.org')
        p = PersonFactory.build(email=factory.LazyAttribute(person_email),
                                user=None,
                                source=person_source_type.DISSERTATION)
        with self.assertRaises(AttributeError):
            p.save()

    @override_settings(INTERNAL_EMAIL_SUFIX='osis.org')
    def test_person_from_internal_source(self):
        person_email = functools.partial(generate_person_email, domain='osis.org')

        p = PersonFactory.build(email=factory.LazyAttribute(person_email),
                                user=None)

        with self.assertDontRaises():
            p.save()

    @override_settings(INTERNAL_EMAIL_SUFIX='osis.org')
    def test_person_without_source(self):
        person_email = functools.partial(generate_person_email, domain='osis.org')
        p = PersonFactory.build(email=factory.LazyAttribute(person_email),
                                user=None,
                                source=None)

        with self.assertDontRaises():
            p.save()
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
import functools
import contextlib
import factory
import datetime

from django.contrib.auth.models import Group
from django.test import TestCase
from django.test import override_settings
from base.models import person
from base.models.enums import person_source_type
from base.tests.factories.user import UserFactory
from base.models.person import CENTRAL_MANAGER_GROUP, FACULTY_MANAGER_GROUP, get_user_interface_language, \
    change_language
from base.tests.factories.person import PersonFactory, generate_person_email, PersonWithoutUserFactory
from base.tests.factories import user


def create_person(first_name, last_name, email=None):
    a_person = person.Person(first_name=first_name, last_name=last_name, email=email)
    a_person.save()
    return a_person


def create_person_with_user(usr):
    a_person = person.Person(first_name=usr.first_name, last_name=usr.last_name, user=usr)
    a_person.save()
    return a_person


class PersonTestCase(TestCase):
    @contextlib.contextmanager
    def assertDontRaise(self):
        try:
            yield
        except AttributeError:
            self.fail('Exception not excepted')


class PersonTest(PersonTestCase):
    def setUp(self):
        self.an_user = user.UserFactory(username="user_without_person")
        self.user_for_person = user.UserFactory(username="user_with_person")
        self.person_with_user = PersonFactory(user=self.user_for_person, language="fr-be", first_name="John",
                                              last_name="Doe")
        self.person_without_user = PersonWithoutUserFactory()

    def test_find_by_id(self):
        tmp_person = PersonFactory()
        db_person = person.find_by_id(tmp_person.id)
        self.assertIsNotNone(tmp_person.user)
        self.assertEqual(db_person.id, tmp_person.id)
        self.assertEqual(db_person.email, tmp_person.email)

    @override_settings(INTERNAL_EMAIL_SUFFIX='osis.org')
    def test_person_from_extern_source(self):
        person_email = functools.partial(generate_person_email, domain='osis.org')
        p = PersonWithoutUserFactory.build(email=factory.LazyAttribute(person_email),
                                           source=person_source_type.DISSERTATION)
        with self.assertRaises(AttributeError):
            p.save()

    @override_settings(INTERNAL_EMAIL_SUFFIX='osis.org')
    def test_person_from_internal_source(self):
        person_email = functools.partial(generate_person_email, domain='osis.org')
        p = PersonWithoutUserFactory.build(email=factory.LazyAttribute(person_email))
        with self.assertDontRaise():
            p.save()

    @override_settings(INTERNAL_EMAIL_SUFFIX='osis.org')
    def test_person_without_source(self):
        person_email = functools.partial(generate_person_email, domain='osis.org')
        p = PersonWithoutUserFactory.build(email=factory.LazyAttribute(person_email),
                                           source=None)
        with self.assertDontRaise():
            p.save()

    def test_find_by_global_id(self):
        a_person = person.Person(global_id="123")
        a_person.save()
        dupplicated_person = person.Person(global_id="123")
        dupplicated_person.save()
        found_person = person.find_by_global_id("1234")
        return self.assertEqual(found_person, None, "find_by_global_id should return None if a record is not found.")

    def test_search_employee(self):
        a_lastname = "Dupont"
        a_firstname = "Marcel"
        a_person = person.Person(last_name=a_lastname,
                                 first_name=a_firstname,
                                 employee=True)
        a_person.save()
        self.assertEqual(person.search_employee(a_lastname)[0], a_person)
        self.assertEqual(len(person.search_employee("{}{}".format(a_lastname, a_firstname))), 0)
        self.assertEqual(person.search_employee("{} {}".format(a_lastname, a_firstname))[0], a_person)
        self.assertIsNone(person.search_employee(None))
        self.assertEqual(len(person.search_employee("zzzzzz")), 0)

        a_person_2 = person.Person(last_name=a_lastname,
                                   first_name="Hervé",
                                   employee=True)
        a_person_2.save()
        self.assertEqual(len(person.search_employee(a_lastname)), 2)
        self.assertEqual(len(person.search_employee("{} {}".format(a_lastname, a_firstname))), 1)

    def test_change_to_invalid_language(self):
        user = UserFactory()
        user.save()
        a_person = create_person_with_user(user)
        person.change_language(user, 'ru')
        self.assertNotEquals(a_person.language, "ru")

    def test_change_language(self):
        user = UserFactory()
        user.save()
        create_person_with_user(user)
        person.change_language(user, "en")
        a_person = person.find_by_user(user)
        self.assertEquals(a_person.language, "en")

    def test_calculate_age(self):
        a_person = PersonFactory()
        a_person.birth_date = datetime.datetime.now() - datetime.timedelta(days=((30*365)+15))
        self.assertEqual(person.calculate_age(a_person), 30)
        a_person.birth_date = datetime.datetime.now() - datetime.timedelta(days=((30*365)-5))
        self.assertEqual(person.calculate_age(a_person), 29)

    def test_is_central_manager(self):
        a_person = PersonFactory()
        self.assertFalse(a_person.is_central_manager())

        a_person.user.groups.add(Group.objects.get(name=CENTRAL_MANAGER_GROUP))
        self.assertTrue(a_person.is_central_manager())

    def test_is_faculty_manager(self):
        a_person = PersonFactory()
        self.assertFalse(a_person.is_faculty_manager())

        a_person.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
        self.assertTrue(a_person.is_faculty_manager())

    def test_show_username_from_person_with_user(self):
        self.assertEqual(self.person_with_user.username(), "user_with_person")

    def test_show_username_from_person_without_user(self):
        self.assertEqual(self.person_without_user.username(), None)

    def test_show_first_name_from_person_with_first_name(self):
        self.assertEqual(self.person_with_user.get_first_name(), self.person_with_user.first_name)

    def test_show_first_name_from_person_without_first_name(self):
        self.person_with_user.first_name = None
        self.person_with_user.save()
        self.assertEqual(self.person_with_user.get_first_name(), self.person_with_user.user.first_name)

    def test_show_first_name_from_person_without_user(self):
        self.person_with_user.first_name = None
        self.person_with_user.user = None
        self.person_with_user.save()
        self.assertEqual(self.person_with_user.get_first_name(), "-")

    def test_get_user_interface_language_with_person_user(self):
        self.assertEqual(get_user_interface_language(self.person_with_user.user), "fr-be")

    def test_get_user_interface_language_with_user_without_person(self):
        self.assertEqual(get_user_interface_language(self.an_user), "fr-be")

    def test_str_function_with_data(self):
        self.person_with_user.middle_name = "Junior"
        self.person_with_user.save()
        self.assertEqual(self.person_with_user.__str__(),"DOE, John Junior")

    def test_change_language_with_user_with_person(self):
        change_language(self.user_for_person, "en")
        self.person_with_user.refresh_from_db()
        self.assertEqual(self.person_with_user.language, "en")

    def test_change_language_with_user_without_person(self):
        self.assertFalse(change_language(self.an_user, "en"))

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
import contextlib
import datetime
import functools

import factory
from django.contrib.auth.models import Group
from django.test import TestCase
from django.test import override_settings

from base.models import person
from base.models.enums import person_source_type
from base.models.enums.groups import CENTRAL_MANAGER_GROUP, FACULTY_MANAGER_GROUP, PROGRAM_MANAGER_GROUP
from base.models.person import get_user_interface_language, \
    change_language
from base.tests.factories import user
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.group import CentralManagerGroupFactory, FacultyManagerGroupFactory, \
    ProgramManagerGroupFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.person import PersonFactory, generate_person_email, PersonWithoutUserFactory, SICFactory, \
    UEFacultyManagerFactory, AdministrativeManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.user import UserFactory


def create_person(first_name, last_name, email="", language=None):
    a_person = person.Person(first_name=first_name, last_name=last_name, email=email, language=language)
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
    @classmethod
    def setUpTestData(cls):
        cls.an_user = user.UserFactory(username="user_without_person")
        cls.user_for_person = user.UserFactory(username="user_with_person")
        cls.person_without_user = PersonWithoutUserFactory()
        CentralManagerGroupFactory()
        FacultyManagerGroupFactory()
        ProgramManagerGroupFactory()

    def setUp(self):
        self.person_with_user = PersonFactory(
            user=self.user_for_person,
            language="fr-be",
            first_name="John",
            last_name="Doe"
        )

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
        self.assertNotEqual(a_person.language, "ru")

    def test_change_language(self):
        user = UserFactory()
        user.save()
        create_person_with_user(user)
        person.change_language(user, "en")
        a_person = person.find_by_user(user)
        self.assertEqual(a_person.language, "en")

    def test_calculate_age(self):
        a_person = PersonFactory()
        a_person.birth_date = datetime.datetime.now() - datetime.timedelta(days=((30 * 365) + 15))
        self.assertEqual(person.calculate_age(a_person), 30)
        a_person.birth_date = datetime.datetime.now() - datetime.timedelta(days=((30 * 365) - 5))
        self.assertEqual(person.calculate_age(a_person), 29)

    def test_is_central_manager(self):
        a_person = PersonFactory()
        self.assertFalse(a_person.is_central_manager)

        del a_person.is_central_manager
        a_person.user.groups.add(Group.objects.get(name=CENTRAL_MANAGER_GROUP))
        self.assertTrue(a_person.is_central_manager)

    def test_is_faculty_manager(self):
        a_person = PersonFactory()
        self.assertFalse(a_person.is_faculty_manager)

        del a_person.is_faculty_manager
        a_person.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
        self.assertTrue(a_person.is_faculty_manager)

    def test_is_faculty_manager_for_ue(self):
        a_person = PersonFactory()
        self.assertFalse(a_person.is_faculty_manager_for_ue)

        a_person = UEFacultyManagerFactory()
        self.assertTrue(a_person.is_faculty_manager_for_ue)

    def test_is_program_manager(self):
        a_person = PersonFactory()
        self.assertFalse(a_person.is_program_manager)

        del a_person.is_program_manager
        a_person.user.groups.add(Group.objects.get(name=PROGRAM_MANAGER_GROUP))
        self.assertTrue(a_person.is_program_manager)

    def test_is_sic(self):
        a_person = PersonFactory()
        self.assertFalse(a_person.is_sic)

        a_person = SICFactory()
        self.assertTrue(a_person.is_sic)

    def test_is_administrative_manager(self):
        a_person = PersonFactory()
        self.assertFalse(a_person.is_administrative_manager)

        a_person = AdministrativeManagerFactory()
        self.assertTrue(a_person.is_administrative_manager)

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

    def test_get_user_interface_language_with_person_without_language(self):
        user_1 = user.UserFactory()
        PersonFactory(user=user_1, language=None)
        self.assertEqual(get_user_interface_language(user_1), "fr-be")

    def test_str_function_with_data(self):
        self.person_with_user.middle_name = "Junior"
        self.person_with_user.save()
        self.assertEqual(self.person_with_user.__str__(), "DOE, John Junior")

    def test_change_language_with_user_with_person(self):
        change_language(self.user_for_person, "en")
        self.person_with_user.refresh_from_db()
        self.assertEqual(self.person_with_user.language, "en")

    def test_change_language_with_user_without_person(self):
        self.assertFalse(change_language(self.an_user, "en"))

    def test_is_linked_to_entity_in_charge_of_learning_unit_year(self):
        person_entity = PersonEntityFactory(person=self.person_with_user)
        luy = LearningUnitYearFactory()

        self.assertFalse(
            self.person_with_user.is_linked_to_entity_in_charge_of_learning_unit_year(luy)
        )

        luy.learning_container_year.requirement_entity = person_entity.entity
        luy.learning_container_year.save()

        self.assertTrue(
            self.person_with_user.is_linked_to_entity_in_charge_of_learning_unit_year(luy)
        )

    def test_is_linked_to_entity_in_charge_of_external_learning_unit_year(self):
        person_entity = PersonEntityFactory(person=self.person_with_user)
        luy = LearningUnitYearFactory()
        ExternalLearningUnitYearFactory(learning_unit_year=luy)

        self.assertFalse(
            self.person_with_user.is_linked_to_entity_in_charge_of_learning_unit_year(luy)
        )

        luy.learning_container_year.requirement_entity = person_entity.entity
        luy.learning_container_year.save()

        self.assertTrue(
            self.person_with_user.is_linked_to_entity_in_charge_of_learning_unit_year(luy)
        )

    def test_managed_programs(self):
        offer_year_1 = OfferYearFactory()
        offer_year_2 = OfferYearFactory()
        ProgramManagerFactory(person=self.person_with_user, offer_year=offer_year_1)
        ProgramManagerFactory(person=self.person_with_user, offer_year=offer_year_2)
        managed_programs = self.person_with_user.get_managed_programs()
        self.assertTrue(len(managed_programs) == 2)
        self.assertTrue(offer_year_1 in managed_programs)
        self.assertTrue(offer_year_2 in managed_programs)

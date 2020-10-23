##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase

from base.models import models_signals as mdl_signals, person as mdl_person
from base.models.person import Person
from base.models.structure import Structure
from base.models.tutor import Tutor
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.group import TutorGroupFactory, ProgramManagerGroupFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory


def get_or_create_user(user_infos):
    a_user, created = User.objects.get_or_create(username=user_infos.get('USERNAME'),
                                                 password=user_infos.get('PASSWORD'))
    if created:
        if user_infos.get('USER_FIRST_NAME'):
            a_user.first_name = user_infos.get('USER_FIRST_NAME')
        if user_infos.get('USER_LAST_NAME'):
            a_user.last_name = user_infos.get('USER_LAST_NAME')
        if user_infos.get('USER_EMAIL'):
            a_user.email = user_infos.get('USER_EMAIL')
        a_user.save()
    return a_user


def get_or_create_person(user=None, first_name=None, global_id=None):
    person = None
    created = False
    if user:
        person = mdl_person.find_by_user(user)
    if not person and global_id:
        person = mdl_person.find_by_global_id(global_id)
    if not person:
        person = Person(user=user, first_name=first_name, global_id=global_id)
        created = True
    if created:
        person.user = user
        person.first_name = first_name
        person.global_id = global_id
    person.save()
    return person


def assert_person_match_user_infos(test_case, person, user_infos):
    test_case.assertEqual(person.first_name, user_infos.get('USER_FIRST_NAME'))
    test_case.assertEqual(person.last_name, user_infos.get('USER_LAST_NAME'))
    test_case.assertEqual(person.global_id, user_infos.get('USER_FGS'))
    test_case.assertEqual(person.email, user_infos.get('USER_EMAIL'))


class CreateUpdatePerson(TestCase):
    def test_create_person_from_user(self):
        user_infos = {
            'USERNAME': 'user1',
            'PASSWORD': 'pass1',
            'USER_FGS': '12345678',
            'USER_FIRST_NAME': 'user1',
            'USER_LAST_NAME': 'User1',
            'USER_EMAIL': 'user1@user.org'
        }
        user = get_or_create_user(user_infos)
        person = mdl_signals._create_update_person(user, None, user_infos)
        assert_person_match_user_infos(self, person, user_infos)

    def test_update_person_with_user_person_given(self):
        user_infos = {
            'USERNAME': 'user2',
            'PASSWORD': 'pass2',
            'USER_FGS': '7777777',
        }
        user = get_or_create_user(user_infos)
        person = get_or_create_person(None, 'first_name_2', None)
        person = mdl_signals._create_update_person(user, person, user_infos)
        self.assertEqual(person.user, user)
        self.assertEqual(person.global_id, user_infos.get('USER_FGS'))
        self.assertEqual(person.first_name, 'first_name_2')


class UpdatePersonIfNecessary(TestCase):
    user_infos = {
        'USERNAME': 'user_test',
        'PASSWORD': 'pass_test',
        'USER_FGS': '22222222',
        'USER_FIRST_NAME': 'user_first',
        'USER_LAST_NAME': 'user_last',
        'USER_EMAIL': 'user1@user.org'}

    def test_necessary_update(self):
        user = get_or_create_user(self.user_infos)
        person = Person(user=None, first_name="user3", last_name="user3", email='test3@test.org', global_id="1111111")
        updated, updated_person = mdl_signals._update_person_if_necessary(user=user,
                                                                          person=person,
                                                                          global_id=self.user_infos.get('USER_FGS'))
        self.assertTrue(updated)
        assert_person_match_user_infos(self, updated_person, self.user_infos)

    def test_unnecessary_update(self):
        user = get_or_create_user(self.user_infos)
        person = Person(user=user,
                        first_name=self.user_infos.get('USER_FIRST_NAME'),
                        last_name=self.user_infos.get('USER_LAST_NAME'),
                        email=self.user_infos.get('USER_EMAIL'),
                        global_id=self.user_infos.get('USER_FGS'))
        updated, updated_person = mdl_signals._update_person_if_necessary(user=user,
                                                                          person=person,
                                                                          global_id=self.user_infos.get('USER_FGS'))
        self.assertFalse(updated)
        assert_person_match_user_infos(self, updated_person, self.user_infos)


class AddToGroupsSignalsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        TutorGroupFactory()
        ProgramManagerGroupFactory()

    def is_member(self, group):
        return self.user_foo.groups.filter(name=group).exists()

    def create_test_tutor(self):
        return Tutor.objects.create(person=self.person_foo)

    def create_test_pgm_manager(self):
        egy = EducationGroupYearFactory(academic_year__current=True)
        offer_year = OfferYearFactory(corresponding_education_group_year=egy)
        return ProgramManagerFactory(offer_year=offer_year, education_group=egy.education_group, person=self.person_foo)

    def create_test_entity_manager(self):
        return EntityManagerFactory(person=self.person_foo, structure=Structure.objects.create(acronym="TEST"))

    def setUp(self):
        self.user_foo = User.objects.create_user('user_foo')
        self.person_foo = Person.objects.create(user=self.user_foo)

    def test_add_to_tutors_group(self):
        self.create_test_tutor()
        self.assertTrue(self.is_member('tutors'), 'user_foo should be in tutors group')

    def test_remove_from_tutors_group(self):
        tutor_foo = self.create_test_tutor()
        tutor_foo.delete()
        self.assertFalse(self.is_member('tutors'), 'user_foo should not be in tutors group anymore')

    def test_add_to_pgm_manager_group(self):
        self.create_test_pgm_manager()
        self.assertTrue(self.is_member('program_managers'), 'user_foo should be in program_managers group')

    def test_remove_from_manager_group(self):
        pgm_manager_foo = self.create_test_pgm_manager()
        pgm_manager_foo.delete()
        self.assertFalse(self.is_member('program_managers'),
                         'user_foo should not be in program_managers group anymore')

    def test_add_to_entity_manager_group(self):
        self.create_test_entity_manager()
        self.assertTrue(self.is_member('entity_managers'),
                        'entity_manager_foo should be in entity_managers group')

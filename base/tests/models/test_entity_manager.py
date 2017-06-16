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

from django.test import TestCase
from base.models import entity_manager
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.structure import StructureFactory
from base.tests.factories.person import PersonFactory
from django.contrib.auth.models import User, Permission


class EntityManagerTest(TestCase):

    def setUp(self):
        self.faculty_administrator = EntityManagerFactory()

        self.user = User.objects.create_user("username", "test@test.com", "passtest",
                                             first_name='first_name', last_name='last_name')
        self.user.save()

    def test_no_entity_manager_for_the_user(self):
        self.assertIsNone(entity_manager.find_entity_manager_by_user(self.user))

    def test_entity_manager_for_the_user(self):
        a_person = PersonFactory(user=self.user)
        entity_mgr = EntityManagerFactory(person=a_person, structure=StructureFactory())
        self.assertEqual(entity_manager.find_entity_manager_by_user(self.user), entity_mgr)


def add_permission(user, codename):
    perm = get_permission(codename)
    user.user_permissions.add(perm)


def get_permission(codename):
    return Permission.objects.get(codename=codename)

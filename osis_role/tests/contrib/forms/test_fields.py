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
from django.test import TestCase

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from education_group.auth.roles.central_manager import CentralManager
from education_group.auth.roles.faculty_manager import FacultyManager
from education_group.auth.scope import Scope
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.auth.faculty_manager import FacultyManagerFactory
from osis_role.contrib.forms.fields import EntityRoleChoiceField


class TestEntityRoleChoiceField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_entity_version = EntityVersionFactory()
        cls.entity_version_level_1 = EntityVersionFactory(parent=cls.root_entity_version.entity)
        cls.entity_version_level_2 = EntityVersionFactory(parent=cls.entity_version_level_1.entity)

    def setUp(self):
        self.person = PersonFactory()
        self.field_instance = EntityRoleChoiceField(person=self.person, group_names=(
            CentralManager.group_name,
            FacultyManager.group_name,
        ))

    def test_case_user_are_linked_with_child_on_role(self):
        CentralManagerFactory(person=self.person, entity=self.root_entity_version.entity, with_child=True)
        self.assertEqual(self.field_instance.get_queryset().count(), 3)

    def test_case_user_are_linked_without_child_on_role(self):
        CentralManagerFactory(person=self.person, entity=self.root_entity_version.entity, with_child=False)
        self.assertEqual(self.field_instance.get_queryset().count(), 1)

    def test_case_user_are_linked_on_multiple_role_connected_to_fields(self):
        CentralManagerFactory(person=self.person, entity=self.root_entity_version.entity, with_child=False)
        FacultyManagerFactory(person=self.person, entity=self.entity_version_level_2.entity, with_child=True)

        self.assertEqual(self.field_instance.get_queryset().count(), 2)

    def test_case_user_has_scope_all_on_entity(self):
        FacultyManagerFactory(person=self.person, entity=self.entity_version_level_2.entity, with_child=True)
        self.assertEquals(self.field_instance.get_queryset().count(), 1)

    def test_case_user_has_other_scope_on_entity(self):
        entity = self.entity_version_level_2.entity
        FacultyManagerFactory(person=self.person, scopes=[Scope.IUFC.value], entity=entity, with_child=True)
        self.assertEquals(self.field_instance.get_queryset().count(), 0)

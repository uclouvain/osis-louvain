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
from unittest import mock

import rules
from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from osis_role.management.commands import sync_perm_role


class TestRoleModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.command_instance = sync_perm_role.Command()

    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name="concrete_role")
        self.mock_role_model = mock.Mock()
        type(self.mock_role_model).group_name = mock.PropertyMock(return_value=self.group.name)
        self.mock_role_model.rule_set = mock.Mock(return_value=rules.RuleSet({
            'base.view_person': rules.always_allow,
            'base.add_person': rules.always_allow,
        }))
        mock_config = {'roles': {self.mock_role_model}}
        patcher_role_manager = mock.patch("osis_role.role.role_manager", **mock_config)
        patcher_role_manager.start()
        self.addCleanup(patcher_role_manager.stop)

    def test_ensure_role_are_sync_with_groups_case_add_multiple_perms(self):
        self.command_instance.handle()

        self.assertEqual(Group.objects.get(name=self.group.name).permissions.count(), 2)

    def test_ensure_group_name_param_specified(self):
        self.command_instance.handle(group="dummy_role")
        #  Ensure concrete_role is not updated
        self.assertEqual(Group.objects.get(name=self.group.name).permissions.count(), 0)

    def test_ensure_role_are_sync_with_groups_remove_perm(self):
        permission_which_are_not_in_role = Permission.objects.get(codename='change_person')
        self.group.permissions.add(permission_which_are_not_in_role)
        self.command_instance.handle()

        qs = Group.objects.get(name=self.group.name).permissions
        self.assertEqual(qs.count(), 2)
        self.assertFalse(qs.filter(codename='change_person').exists())

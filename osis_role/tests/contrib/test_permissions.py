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
import mock
import rules
from django.contrib.auth import models
from django.contrib.auth.models import Group, Permission
from django.db.models import QuerySet
from django.test import TestCase
from rules import RuleSet

from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from osis_role.contrib.permissions import ObjectPermissionBackend, _add_role_queryset_to_perms_context


class TestObjectPermissionBackend(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_class = ObjectPermissionBackend()
        cls.group, _ = Group.objects.get_or_create(name="concrete_role")

    def setUp(self):
        self.person = PersonFactory()
        self.mock_role_model = mock.Mock()
        type(self.mock_role_model).group_name = mock.PropertyMock(return_value=self.group.name)
        self.mock_role_model.rule_set = mock.Mock(return_value=rules.RuleSet({
            'perm_allowed': rules.always_allow,
            'perm_denied': rules.always_deny
        }))

        mock_config = {'roles': {self.mock_role_model}}
        patcher_role_manager = mock.patch("osis_role.role.role_manager", **mock_config)
        patcher_role_manager.start()
        self.addCleanup(patcher_role_manager.stop)

    def test_user_have_no_perms_case_inactive_user(self):
        self.person.user.is_active = False
        self.person.user.save()

        self.assertFalse(self.auth_class.has_perm(self.person.user, 'perm_allowed'))

    def test_user_have_no_perms_case_is_anonymous_user(self):
        self.assertFalse(self.auth_class.has_perm(models.AnonymousUser, 'perm_allowed'))

    def test_user_have_no_perms_case_is_not_assign_to_any_roles(self):
        self.assertFalse(self.auth_class.has_perm(self.person.user, 'perm_allowed'))

    @mock.patch('django.db.models.QuerySet.exists', return_value=True)
    def test_user_have_perms_case_is_assign_to_at_least_one_role(self, mock_queryset_exists):
        self.person.user.groups.add(self.group)

        self.assertTrue(self.auth_class.has_perm(self.person.user, 'perm_allowed'))

    @mock.patch('django.db.models.QuerySet.exists', return_value=True)
    def test_user_have_no_perms_case_is_assign_to_at_least_one_role(self, mock_queryset_exists):
        self.person.user.groups.add(self.group)

        self.assertFalse(self.auth_class.has_perm(self.person.user, 'perm_denied'))

    @mock.patch('django.db.models.QuerySet.exists', return_value=False)
    def test_ensure_that_group_not_managed_by_role_manager_fallback_to_default_behaviour(self, mock_queryset_exists):
        group = Group.objects.create(name='group_not_managed_by_role')
        can_add_user = Permission.objects.get(codename='add_user')
        group.permissions.add(can_add_user)
        self.person.user.groups.add(group)

        perm = "%s.%s" % (can_add_user.content_type.app_label, can_add_user.codename)
        self.assertTrue(self.auth_class.has_perm(self.person.user, perm))


class TestAddRoleQuerysetToRuleSet(TestCase):
    def test_ensure_cache_role_queryset_is_added_to_perms_context(self):
        @rules.predicate(bind=True, name='ensure_role_qs_exist')
        def ensure_role_qs_exist_fn(self, *args, **kwargs):
            if not isinstance(self.context['role_qs'], QuerySet):
                raise Exception
            return True

        qs = QuerySet()
        rule_set = RuleSet()
        rule_set.add_rule('perm_allowed', ensure_role_qs_exist_fn)

        _add_role_queryset_to_perms_context(rule_set, 'perm_allowed', qs)
        self.assertTrue(rule_set.test_rule('perm_allowed', UserFactory()))
